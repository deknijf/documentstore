import hashlib
import imaplib
import uuid
from email import message_from_bytes
from email.header import decode_header
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Document, Group, MailIngestSeen, User


def _decode_mime(value: str | None) -> str:
    if not value:
        return ""
    decoded = decode_header(value)
    out = []
    for part, enc in decoded:
        if isinstance(part, bytes):
            try:
                out.append(part.decode(enc or "utf-8", errors="replace"))
            except Exception:
                out.append(part.decode("utf-8", errors="replace"))
        else:
            out.append(str(part))
    return "".join(out).strip()


def _mailbox_fingerprint(host: str, username: str, folder: str) -> str:
    base = f"{host.strip().lower()}::{username.strip().lower()}::{folder.strip().upper()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _pick_ingest_group(db: Session, tenant_id: str, configured_group_id: str | None, fallback_user_id: str | None) -> str:
    if configured_group_id:
        grp = db.query(Group).filter(Group.id == configured_group_id, Group.tenant_id == tenant_id).first()
        if grp:
            return grp.id
    if fallback_user_id:
        user = db.query(User).filter(User.id == fallback_user_id, User.tenant_id == tenant_id).first()
        if user and user.groups:
            group_ids = sorted([g.id for g in user.groups if str(g.tenant_id or "") == tenant_id])
            if group_ids:
                return group_ids[0]
    admins = db.query(Group).filter(Group.tenant_id == tenant_id, Group.name == "Administrators").first()
    if admins:
        return admins.id
    raise RuntimeError("Geen ingest groep gevonden")


def ingest_mail_pdfs(
    *,
    db: Session,
    host: str,
    port: int,
    username: str,
    password: str,
    folder: str = "INBOX",
    use_ssl: bool = True,
    attachment_types: str = "pdf",
    group_id: str | None = None,
    uploaded_by_user_id: str | None = None,
    tenant_id: str | None = None,
) -> dict:
    host = str(host or "").strip()
    username = str(username or "").strip()
    password = str(password or "")
    folder = str(folder or "INBOX").strip() or "INBOX"
    port = int(port or 993)
    if not host or not username or not password:
        raise RuntimeError("IMAP host, username en password zijn verplicht")

    allowed_exts = {
        x.strip().lower().lstrip(".")
        for x in str(attachment_types or "pdf").split(",")
        if x.strip()
    }
    if not allowed_exts:
        allowed_exts = {"pdf"}

    ingest_group_id = _pick_ingest_group(db, tenant_id, group_id, uploaded_by_user_id)
    mailbox_fp = _mailbox_fingerprint(host, username, folder)

    client = imaplib.IMAP4_SSL(host, port) if use_ssl else imaplib.IMAP4(host, port)
    imported = 0
    skipped_seen = 0
    scanned_messages = 0
    document_ids: list[str] = []
    try:
        client.login(username, password)
        status, _ = client.select(folder, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Kan mailbox-folder niet openen: {folder}")
        status, data = client.uid("search", None, "ALL")
        if status != "OK":
            return {"imported": 0, "skipped_seen": 0, "scanned_messages": 0}
        uids = data[0].split() if data and data[0] else []
        for uid_raw in uids:
            uid = uid_raw.decode("utf-8", errors="ignore")
            if not uid:
                continue
            scanned_messages += 1
            status, msg_data = client.uid("fetch", uid, "(RFC822)")
            if status != "OK" or not msg_data:
                continue
            raw_bytes = None
            for item in msg_data:
                if isinstance(item, tuple) and len(item) > 1:
                    raw_bytes = item[1]
                    break
            if not raw_bytes:
                continue
            msg = message_from_bytes(raw_bytes)
            for part in msg.walk():
                if part.is_multipart():
                    continue
                filename = _decode_mime(part.get_filename())
                if not filename:
                    continue
                ext = Path(filename).suffix.lower().lstrip(".")
                if ext not in allowed_exts:
                    continue
                seen = (
                    db.query(MailIngestSeen)
                    .filter(
                        MailIngestSeen.tenant_id == tenant_id,
                        MailIngestSeen.mailbox_fingerprint == mailbox_fp,
                        MailIngestSeen.message_uid == uid,
                        MailIngestSeen.attachment_name == filename,
                    )
                    .first()
                )
                if seen:
                    skipped_seen += 1
                    continue

                payload = part.get_payload(decode=True) or b""
                if not payload:
                    continue
                content_hash = hashlib.sha256(payload).hexdigest()

                # Extra dedupe by payload hash per mailbox.
                seen_hash = (
                    db.query(MailIngestSeen)
                    .filter(
                        MailIngestSeen.tenant_id == tenant_id,
                        MailIngestSeen.mailbox_fingerprint == mailbox_fp,
                        MailIngestSeen.content_sha256 == content_hash,
                    )
                    .first()
                )
                if seen_hash:
                    db.add(
                        MailIngestSeen(
                            tenant_id=tenant_id,
                            mailbox_fingerprint=mailbox_fp,
                            message_uid=uid,
                            attachment_name=filename,
                            content_sha256=content_hash,
                            document_id=seen_hash.document_id,
                        )
                    )
                    db.commit()
                    skipped_seen += 1
                    continue

                document_id = str(uuid.uuid4())
                storage_name = f"{document_id}.pdf"
                file_path = Path(settings.uploads_dir) / storage_name
                file_path.write_bytes(payload)

                doc = Document(
                    id=document_id,
                    tenant_id=tenant_id,
                    filename=filename,
                    content_type="application/pdf",
                    file_path=str(file_path),
                    group_id=ingest_group_id,
                    uploaded_by_user_id=uploaded_by_user_id,
                    paid=False,
                    ocr_processed=False,
                    ai_processed=False,
                    status="uploaded",
                )
                db.add(doc)
                db.commit()

                db.add(
                    MailIngestSeen(
                        tenant_id=tenant_id,
                        mailbox_fingerprint=mailbox_fp,
                        message_uid=uid,
                        attachment_name=filename,
                        content_sha256=content_hash,
                        document_id=document_id,
                    )
                )
                db.commit()
                imported += 1
                document_ids.append(document_id)
    finally:
        try:
            client.logout()
        except Exception:
            pass

    return {
        "imported": imported,
        "skipped_seen": skipped_seen,
        "scanned_messages": scanned_messages,
        "document_ids": document_ids,
    }
    tenant_id = str(tenant_id or "").strip()
    if not tenant_id:
        raise RuntimeError("Tenant is verplicht voor mail ingest")
