import pytest

from agentic.task_graphs.annual_report_task_graph import AnnualReportTaskGraph


def test_load_incidents_missing_file(monkeypatch):
    tg = AnnualReportTaskGraph()
    monkeypatch.setattr(
        tg, "load_incidents", lambda ctx: (_ for _ in ()).throw(FileNotFoundError())
    )
    with pytest.raises(FileNotFoundError):
        tg.execute()


def test_load_ess_items_missing_file(monkeypatch):
    tg = AnnualReportTaskGraph()
    monkeypatch.setattr("os.path.exists", lambda _: False)
    with pytest.raises(FileNotFoundError):
        tg.load_ess_items({})
