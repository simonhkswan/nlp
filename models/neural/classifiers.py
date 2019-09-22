import logging
import os
import random
import numpy as np
import tensorflow as tf
from models.base import Model

logger = logging.getLogger(__name__)


class LSTMParaClassifier(Model):

    def __init__(self, input_dim, dims, max_len):
        self.in_dim = input_dim
        self.dims = dims
        self.max_len = max_len
        self.sess, self.graph = None, None
        self.x, self.y = None, None
        self.labels, self.loss, self.train = None, None, None
        self.cell_weights = None

        fe = None
        super(LSTMParaClassifier, self).__init__(
            in_type="Paragraph", out_type="Boolean",
            feature_extractor=fe
        )

    def construct(self):
        self.graph = tf.Graph()
        with self.graph.as_default():
            self.x = tf.placeholder(dtype=tf.float32,
                                    shape=[None, self.max_len, self.in_dim])
            if self.cell_weights is None:
                self.cells = [tf.keras.layers.LSTMCell(
                    d,
                    kernel_initializer=tf.constant_initializer(
                        0.001*np.ones([d*2, d*4], dtype=np.float32)
                    ),
                    # recurrent_initializer=tf.constant_initializer(
                    #     0.00001*np.ones([d, d * 4], dtype=np.float32)
                    # )
                ) for d in self.dims]
            else:
                self.cells = [
                    tf.keras.layers.LSTMCell(
                        d[0],
                        kernel_initializer=d[1],
                        recurrent_initializer=d[2],
                        bias_initializer=d[3]
                    )
                    for d in self.cell_weights
                ]
            rnn = tf.keras.layers.RNN(self.cells, return_state=True)
            dense = tf.keras.layers.Dense(16)
            dense2 = tf.keras.layers.Dense(1)
            self.y = dense2(dense(rnn(self.x)[0]))
            self.labels = tf.placeholder(dtype=tf.float32,
                                         shape=[None, 1])
            self.loss = tf.reduce_mean(
                tf.nn.sigmoid_cross_entropy_with_logits(
                    logits=self.y, labels=self.labels
                )
            )
            optimiser = tf.train.AdadeltaOptimizer()
            tf.summary.scalar("CrossEntropyLoss", self.loss)
            self.train = optimiser.minimize(self.loss)

    def predict(self, x):
        pass

    def train_model(self, data, epochs, log_dir):
        logger.info("Starting training for LSTMParaClassifier with %d examples,"
                    " %d epochs. Saving logs to %s", len(data), epochs, log_dir)
        config = tf.ConfigProto(intra_op_parallelism_threads=4,
                                inter_op_parallelism_threads=4)
        self.sess = tf.Session(graph=self.graph, config=config)
        writer = tf.summary.FileWriter(logdir=log_dir, graph=self.graph,
                                       session=self.sess)
        with self.graph.as_default():
            print(tf.global_variables())
            self.sess.run(tf.global_variables_initializer())
            merged = tf.summary.merge_all()
            writer.add_graph(self.graph)
            for e in range(epochs):
                logger.info("Starting epoch %d.", e+1)
                random.shuffle(data)
                for step, (x, l) in enumerate(data):
                    _, summary = self.sess.run(
                        [self.train, merged],
                        feed_dict={self.x: x, self.labels: l}
                    )
                    writer.add_summary(summary, e*len(data)+step)
                # self.to_json()

    def to_json(self):
        for cell in self.cells:
            print(self.sess.run(cell.kernel))
            print(self.sess.run(cell.recurrent_kernel))
            # print(self.sess.run(cell.bias))

    @staticmethod
    def from_json(json_dict):
        pass
