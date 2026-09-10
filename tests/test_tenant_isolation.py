"""A document outside the caller's tenant must be indistinguishable from one
that does not exist. A 403 here confirmed the id to another tenant."""

MISSING_ID = "00000000-0000-0000-0000-000000000000"


def test_reading_another_tenants_document_returns_not_found(client, tenant_b, document_a):
    assert client.get(f"/api/documents/{document_a}", headers=tenant_b["auth"]).status_code == 404


def test_unknown_id_is_indistinguishable_from_another_tenants_document(client, tenant_b, document_a):
    foreign = client.get(f"/api/documents/{document_a}", headers=tenant_b["auth"])
    missing = client.get(f"/api/documents/{MISSING_ID}", headers=tenant_b["auth"])
    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json()


def test_updating_another_tenants_document_returns_not_found(client, tenant_b, document_a):
    response = client.put(
        f"/api/documents/{document_a}", json={"subject": "overgenomen"}, headers=tenant_b["auth"]
    )
    assert response.status_code == 404


def test_downloading_another_tenants_document_returns_not_found(client, tenant_b, document_a):
    assert client.get(f"/files/{document_a}", headers=tenant_b["auth"]).status_code == 404


def test_reprocessing_another_tenants_document_returns_not_found(client, tenant_b, document_a):
    response = client.post(f"/api/documents/{document_a}/reprocess", headers=tenant_b["auth"])
    assert response.status_code == 404


def test_setting_labels_on_another_tenants_document_returns_not_found(client, tenant_b, document_a):
    response = client.put(
        f"/api/documents/{document_a}/labels", json={"label_ids": []}, headers=tenant_b["auth"]
    )
    assert response.status_code == 404


def test_document_list_is_scoped_to_the_callers_tenant(client, tenant_a, tenant_b, document_a):
    ids_a = {d["id"] for d in client.get("/api/documents", headers=tenant_a["auth"]).json()}
    ids_b = {d["id"] for d in client.get("/api/documents", headers=tenant_b["auth"]).json()}
    assert document_a in ids_a
    assert document_a not in ids_b
    assert not ids_a & ids_b


def test_search_is_scoped_to_the_callers_tenant(client, tenant_a, tenant_b, document_a):
    client.put(
        f"/api/documents/{document_a}",
        json={"subject": "grensgeval-zoekterm"},
        headers=tenant_a["auth"],
    )
    hits_a = client.get("/api/search?q=grensgeval-zoekterm", headers=tenant_a["auth"]).json()
    hits_b = client.get("/api/search?q=grensgeval-zoekterm", headers=tenant_b["auth"]).json()
    assert document_a in {d["id"] for d in hits_a}
    assert hits_b == []
