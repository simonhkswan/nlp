from itertools import zip_longest
from neo4j import GraphDatabase
from data.structures import Paragraph, Document
import logging

logger = logging.getLogger(__name__)


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks

    Examples:
        grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


class GraphCon(object):
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def query(self, query):
        with self._driver.session() as session:
            result = session.write_transaction(self._query, query)
            return result

    @staticmethod
    def _query(tx, query):
        result = tx.run(query)
        return result.records()

    def add_document(self, did, title):
        with self._driver.session() as session:
            doc = session.write_transaction(self._create_and_return_doc,
                                            did, title)
            logger.log(16, 'neo4j: %s' % doc)

    @staticmethod
    def _create_and_return_doc(tx, did, title):
        result = tx.run(
                "CREATE (d:Document) "
                "SET d.doc_id = $did, d.title = $title "
                "RETURN d.title + ', from node ' + id(d) ",
                did=did,
                title=title
        )
        return result.single()[0]

    def get_documents(self, limit, batch_size=1):
        for ids in grouper(range(limit), batch_size):
            with self._driver.session() as session:
                docs = session.write_transaction(self._return_doc, list(ids))
            for doc in docs:
                yield Document(
                    paragraphs=doc.get('paragraphs'),
                    title=doc.get('d').get('title'),
                    node_id=doc.get('d').id,
                    bowv=doc.get('d').get('bowv')
                )

    @staticmethod
    def _return_doc(tx, ids):
        logger.log(16, "Fetching %d Document(s) (ids: %d-%d)." %
                   (len(ids), ids[0], ids[-1]))
        result = tx.run(
                "MATCH (d:Document)-[:contains]->(p:Paragraph) "
                "WHERE d.doc_id in $doc_ids "
                "RETURN d, COLLECT(p) as paragraphs ",
                doc_ids=ids
        )
        return result.records()

    def get_document_from_title(self, title):
        with self._driver.session() as session:
            docs = session.write_transaction(
                self._return_doc_from_title, title
            )
            doc = next(docs)
            return Document(
                paragraphs=doc.get('paragraphs'),
                title=doc.get('d').get('title'),
                id=doc.get('d').id,
                bowv=doc.get('d').get('bowv')
            )

    @staticmethod
    def _return_doc_from_title(tx, title):
        logger.log(16, "Fetching Document with title %s." % title)
        result = tx.run(
                "MATCH (d:Document)-[:contains]->(p:Paragraph) "
                "WHERE d.title = $title "
                "RETURN d, COLLECT(p) as paragraphs ",
                title=title
        )
        return result.records()

    def add_paragraph(self, pid, did, text):
        with self._driver.session() as session:
            para = session.write_transaction(self._create_and_return_para, pid,
                                             did, text)
            logger.log(15, 'neo4j: %s' % para)

    @staticmethod
    def _create_and_return_para(tx, pid, did, text):
        result = tx.run(
                "MATCH (d:Document) "
                "WHERE d.doc_id = $did "
                "CREATE r = (d)-[:contains]->"
                "(p:Paragraph {pid: $pid, text: $text}) "
                "RETURN r",
                did=did,
                pid=pid,
                text=text
        )
        return result.single()[0]

    def link_documents(self, title_a, title_b):
        with self._driver.session() as session:
            link = session.write_transaction(self._link_documents, title_a,
                                             title_b)
            logger.log(16, 'neo4j: %s' % link)

    @staticmethod
    def _link_documents(tx, title_a, title_b):
        result = tx.run(
                "MATCH (d:Document), (f:Document) "
                "WHERE d.title = $titlea AND f.title=$titleb "
                "CREATE r = (d)-[:references]->(f) "
                "RETURN r ",
                titlea=title_a,
                titleb=title_b
        )
        return result.single()[0]

    def get_paragraphs_by_doc_id(self, doc_id):
        with self._driver.session() as session:
            paras = session.write_transaction(self._get_paragraphs, doc_id)
            logger.log(16, 'neo4j: %s' % paras)
        for p in paras:
            yield Paragraph(
                text=p.get('p').get('text'),
                id=p.get('p').id
            )

    @staticmethod
    def _get_paragraphs(tx, did):
        result = tx.run(
                "MATCH (d:Document)-[:contains]->(p:Paragraph) "
                "WHERE d.doc_id = $did "
                "RETURN p ORDER BY p.pid",
                did=did
        )
        return result.records()

    def set_node_bowv(self, node_id, bowv):
        with self._driver.session() as session:
            node = session.write_transaction(
                self._set_node_bowv, node_id, bowv
            )
            logger.log(16, 'neo4j: %s' % node)

    @staticmethod
    def _set_node_bowv(tx, node_id, bowv):
        result = tx.run(
                "MATCH (n) "
                "WHERE id(n) = $node_id "
                "SET n.bowv = $bowv "
                "RETURN 'bowv set for ' + id(n) ",
                node_id=node_id,
                bowv=bowv
        )
        return result.single()
