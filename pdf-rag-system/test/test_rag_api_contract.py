import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import Base, Document, User
from routers import rag as rag_router


class RagApiContractTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.SessionLocal()
        self.user = User(id=7, username="tester", hashed_password="secret")
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)

        self.app = FastAPI()
        self.app.include_router(rag_router.router)
        self.app.dependency_overrides[rag_router.get_db] = self._override_get_db
        self.app.dependency_overrides[rag_router.get_current_user] = self._override_get_current_user
        self.client = TestClient(self.app)
        self.reports_dir_patch = patch.object(rag_router, "FINANCIAL_REPORTS_DIR", self.temp_dir.name)
        self.reports_dir_patch.start()

    def tearDown(self):
        self.reports_dir_patch.stop()
        self.client.close()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()
        self.temp_dir.cleanup()

    def _override_get_db(self):
        yield self.db

    def _override_get_current_user(self):
        return self.user

    def _add_document(self, source_name: str = "report.pdf", title: str = "测试报告"):
        doc = Document(
            user_id=self.user.id,
            source="upload",
            title=title,
            pdf_path=f"financial_reports/user_{self.user.id}/{source_name}",
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def test_search_endpoint_trims_query_and_forwards_filters(self):
        retrieve_mock = AsyncMock(return_value=[
            {
                "text": "营收同比增长 18%",
                "source": "report.pdf",
                "page_number": 3,
                "chunk_index": 0,
                "is_table": False,
                "document_id": 12,
                "file_type": "pdf",
                "score": 0.83,
            }
        ])

        with patch.object(rag_router, "retrieve", retrieve_mock):
            response = self.client.post(
                "/api/rag/search",
                json={
                    "query": "  营收情况  ",
                    "top_k": 80,
                    "document_ids": [12, 12, 13],
                    "score_threshold": 0.72,
                    "file_types": ["pdf", "pdf", "word"],
                    "sort_by": "page_asc",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["query"], "营收情况")
        self.assertEqual(payload["top_k"], 50)
        self.assertEqual(payload["score_threshold"], 0.72)
        self.assertEqual(payload["file_types"], ["pdf", "word"])
        self.assertEqual(payload["sort_by"], "page_asc")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["results"][0]["source"], "report.pdf")
        retrieve_mock.assert_awaited_once_with(
            query="营收情况",
            user_id=self.user.id,
            top_k=50,
            document_ids=[12, 13],
            score_threshold=0.72,
            file_types=["pdf", "word"],
            sort_by="page_asc",
        )

    def test_search_endpoint_rejects_blank_query(self):
        response = self.client.post(
            "/api/rag/search",
            json={"query": "   ", "top_k": 5},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "query 不能为空")

    def test_search_endpoint_rejects_invalid_file_type(self):
        response = self.client.post(
            "/api/rag/search",
            json={"query": "测试", "file_types": ["ppt"]},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("不支持的 file_types", response.json()["detail"])

    def test_indexed_endpoint_enriches_document_metadata(self):
        doc = self._add_document()
        file_path = Path(self.temp_dir.name) / f"user_{self.user.id}" / "report.pdf"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = b"fake-pdf-content"
        file_path.write_bytes(content)

        with patch.object(rag_router, "list_indexed_documents", return_value=[{"source": "report.pdf", "count": 4}]):
            response = self.client.get("/api/rag/indexed")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["sources"]), 1)
        source = payload["sources"][0]
        self.assertEqual(source["source"], "report.pdf")
        self.assertEqual(source["count"], 4)
        self.assertEqual(source["document_id"], doc.id)
        self.assertEqual(source["title"], "测试报告")
        self.assertEqual(source["pdf_path"], f"financial_reports/user_{self.user.id}/report.pdf")
        self.assertEqual(source["file_size"], len(content))
        self.assertIsNotNone(source["created_at"])

    def test_document_detail_endpoint_returns_exact_chunks(self):
        doc = self._add_document(source_name="detail.pdf", title="详情文档")
        chunks_mock = Mock(return_value=[
            {
                "text": "第一页内容",
                "source": "detail.pdf",
                "page_number": 1,
                "chunk_index": 0,
                "is_table": False,
                "document_id": doc.id,
            },
            {
                "text": "第二页表格",
                "source": "detail.pdf",
                "page_number": 2,
                "chunk_index": 1,
                "is_table": True,
                "document_id": doc.id,
            },
        ])

        with patch.object(rag_router, "get_document_chunks", chunks_mock):
            response = self.client.get("/api/rag/document/detail.pdf?limit=2")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source"], "detail.pdf")
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["document_id"], doc.id)
        self.assertEqual(payload["title"], "详情文档")
        self.assertEqual(payload["chunks"][1]["is_table"], True)
        chunks_mock.assert_called_once_with(self.user.id, "detail.pdf", limit=2)

    def test_delete_document_endpoint_removes_db_record(self):
        doc = self._add_document(source_name="delete-me.pdf", title="待删除")

        with patch.object(rag_router, "delete_document_vectors", return_value={"status": "ok", "deleted": 6}):
            response = self.client.delete("/api/rag/document/delete-me.pdf")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["deleted"], 6)
        self.assertEqual(payload["document_id"], doc.id)
        self.assertTrue(payload["document_deleted"])
        self.assertIsNone(self.db.query(Document).filter(Document.id == doc.id).first())

    def test_ingest_upload_stores_files_under_user_directory_and_reuses_document(self):
        ingest_mock = AsyncMock(side_effect=[
            {"status": "ok", "chunks": 3, "source": "report.pdf"},
            {"status": "ok", "chunks": 5, "source": "report.pdf"},
        ])

        with patch.object(rag_router, "ingest_pdf", ingest_mock):
            first = self.client.post(
                "/api/rag/ingest/upload",
                files={"file": ("report.pdf", b"first-version", "application/pdf")},
            )
            second = self.client.post(
                "/api/rag/ingest/upload",
                files={"file": ("report.pdf", b"second-version", "application/pdf")},
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        docs = self.db.query(Document).filter(Document.user_id == self.user.id).all()
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].pdf_path, f"financial_reports/user_{self.user.id}/report.pdf")
        saved_path = Path(self.temp_dir.name) / f"user_{self.user.id}" / "report.pdf"
        self.assertTrue(saved_path.exists())
        self.assertEqual(saved_path.read_bytes(), b"second-version")
        self.assertEqual(first.json()["document_id"], second.json()["document_id"])
        self.assertEqual(ingest_mock.await_count, 2)
        first_call = ingest_mock.await_args_list[0]
        self.assertEqual(first_call.args[0], str(saved_path))
        self.assertEqual(first_call.args[1], self.user.id)
        self.assertEqual(first_call.kwargs["document_id"], first.json()["document_id"])

    def test_manual_ingest_by_document_id_resolves_user_pdf_path(self):
        doc = self._add_document(source_name="manual.pdf", title="手动入库")
        saved_path = Path(self.temp_dir.name) / f"user_{self.user.id}" / "manual.pdf"
        saved_path.parent.mkdir(parents=True, exist_ok=True)
        saved_path.write_bytes(b"manual-pdf")

        ingest_mock = AsyncMock(return_value={"status": "ok", "chunks": 2, "source": "manual.pdf", "document_id": doc.id})
        with patch.object(rag_router, "ingest_pdf", ingest_mock):
            response = self.client.post("/api/rag/ingest", json={"document_id": doc.id})

        self.assertEqual(response.status_code, 200)
        ingest_mock.assert_awaited_once_with(str(saved_path), self.user.id, document_id=doc.id)

    def test_batch_upload_returns_summary_with_partial_failures(self):
        ingest_mock = AsyncMock(side_effect=[
            {"status": "ok", "chunks": 4, "source": "alpha.pdf"},
            {"status": "error", "message": "PDF 解析结果为空"},
        ])

        with patch.object(rag_router, "ingest_pdf", ingest_mock):
            response = self.client.post(
                "/api/rag/ingest/batch-upload",
                files=[
                    ("files", ("alpha.pdf", b"alpha", "application/pdf")),
                    ("files", ("broken.pdf", b"broken", "application/pdf")),
                    ("files", ("notes.txt", b"not-pdf", "text/plain")),
                ],
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "partial")
        self.assertEqual(payload["summary"], {"total": 3, "success": 1, "failed": 2, "chunks": 4})
        self.assertEqual(payload["results"][0]["status"], "ok")
        self.assertEqual(payload["results"][0]["filename"], "alpha.pdf")
        self.assertEqual(payload["results"][1]["message"], "PDF 解析结果为空")
        self.assertEqual(payload["results"][2]["filename"], "notes.txt")
        self.assertEqual(payload["results"][2]["status"], "error")
        self.assertEqual(ingest_mock.await_count, 2)


if __name__ == "__main__":
    unittest.main()
