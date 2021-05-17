import logging
import os
import numpy as np
import tensorflow as tf
from models.base import Model
from models.feature_extractors import FeatureExtractor, SkipGramExtractor

logger = logging.getLogger(__name__)

W2V_DIR = "/home/simonhkswan/code/nlp/generated/word2vec/1"
if not os.path.exists(W2V_DIR):
    os.makedirs(W2V_DIR)


class Word2Vec(Model, FeatureExtractor):
    class_name = "Word2Vec"

    def __init__(self, dim=128, vocab_len=50000, **kwargs):
        self.dim = dim
        self.vocab_length = vocab_len
        self.graph = None
        self.sess = None
        self.emb_weights, self.loss = None, None
        self.x, self.y = None, None
        self.word_vectors = kwargs.get('word_vectors', None)
        self.vocab = kwargs.get('vocab', None)
        self.w2v = None
        self.make_w2v()
        logger.info("Word2Vec initialised. dim: %d, vocab_len: %d" %
                    (self.dim, self.vocab_length))
        super(Word2Vec, self).__init__(
            in_type="Corpora", out_type=None,
            feature_extractor=SkipGramExtractor(window=kwargs.get("window")),
            in_types=["Paragraph"], class_name="Word2Vec"
        )

    def make_w2v(self):
        if self.word_vectors is not None and self.vocab is not None:
            logger.info("Constructing word2vector dictionary.")
            self.w2v = {w: self.word_vectors[n, :]
                        for n, w in enumerate(self.vocab)}

    def construct(self):
        logger.info('Constructing Word2Vec model with dim: %d, vocab_length: %d'
                    % (self.dim, self.vocab_length))
        self.graph = tf.Graph()

        with self.graph.as_default():
            self.x = tf.placeholder(tf.int32, [None, ])
            self.y = tf.placeholder(tf.int32, [None, None])

            # Embedding
            self.emb_weights = tf.Variable(
                initial_value=np.random.normal(
                    loc=0.0,
                    scale=(1 / 10),
                    size=[self.vocab_length, self.dim]
                ),
                trainable=True,
                dtype=tf.float32
            )

            wv = tf.nn.embedding_lookup(self.emb_weights, self.x)

            fc_weights = tf.Variable(
                initial_value=np.random.normal(
                    loc=0.0,
                    scale=(1 / 10),
                    size=[self.vocab_length, self.dim]
                ),
                trainable=True,
                dtype=tf.float32
            )

            fc_bias = tf.Variable(
                initial_value=np.zeros([self.vocab_length], dtype=np.float32),
                trainable=True,
                dtype=np.float32
            )

            loss = tf.nn.nce_loss(
                fc_weights,
                fc_bias,
                labels=self.y,
                inputs=wv,
                num_sampled=20,
                num_classes=self.vocab_length,
                num_true=4
            )
            self.loss = tf.reduce_mean(loss)
            tf.summary.scalar('Loss', self.loss)

    def train(self, x, y, mbs=5000, steps=300000):
        logger.info('Training Word2Vec model. X: %s Y: %s.' %
                    (x.shape, y.shape))
        n = int(x.shape[0]/mbs)
        with self.graph.as_default():
            opt = tf.train.GradientDescentOptimizer(1)
            train = opt.minimize(self.loss)
            self.sess = tf.Session(graph=self.graph)
            self.sess.run(tf.global_variables_initializer())
            merge = tf.summary.merge_all()
            writer = tf.summary.FileWriter(logdir=W2V_DIR,
                                           graph=self.graph, session=self.sess)
            saver = tf.train.Saver(max_to_keep=1)
            for s in range(steps):
                if s % 1000 == 0:
                    _, summary = self.sess.run(
                        [train, merge],
                        feed_dict={
                            self.x: x[s % n*mbs:(s % n+1)*mbs],
                            self.y: y[s % n*mbs:(s % n+1)*mbs]
                        }
                    )
                    writer.add_summary(summary, s)
                    saver.save(sess=self.sess, save_path=W2V_DIR+'/w2v.ckpt',
                               global_step=s)
                else:
                    _ = self.sess.run(
                        train,
                        feed_dict={
                            self.x: x[s % n * mbs:(s % n + 1) * mbs],
                            self.y: y[s % n * mbs:(s % n + 1) * mbs]
                        }
                    )

                if (s+1) % 100000 == 0:
                    self.save(W2V_DIR)

    def save(self, path):
        logger.info("Saving Word2Vec to %s." % path)
        wv = self.sess.run(self.emb_weights)
        np.save(path + '/wordvectors.npy', wv)
        self.fe.save_vocab_tsv(path=path+'/vocab.tsv')

    def to_json(self):
        pass

    @staticmethod
    def from_json(json_dict):
        pass

    @staticmethod
    def load(path):
        logger.info("Loading Word2Vec from %s." % path)
        counts = [l[:-1].split('\t')
                  for l in open(path+'/vocab.tsv', 'r').readlines()[1:]]
        word_vectors = np.load(path+'/wordvectors.npy')[0]
        logger.debug('Word vectors shape: %s, Counts length: %d' %
                     (word_vectors.shape, len(counts)))
        w2v = Word2Vec(
            word_vectors=word_vectors,
            vocab=[c[0] for c in counts]
        )
        return w2v

    def __getitem__(self, item):
        if type(item) is str:
            return self.w2v.get(item, self.w2v['<UNK>'])
        elif type(item) is list:
            return [self.w2v.get(w, self.w2v['<UNK>']) for w in item]
        
    def predict(self, x):
        return self[x]

    def extract(self, node):
        return self[[w for w in node.words(lower=True)]]
