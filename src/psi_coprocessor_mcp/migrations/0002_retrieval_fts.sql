CREATE VIRTUAL TABLE IF NOT EXISTS retrieval_documents_fts
USING fts5(
    title,
    content,
    tags,
    metadata,
    content='retrieval_documents',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS retrieval_documents_ai AFTER INSERT ON retrieval_documents BEGIN
    INSERT INTO retrieval_documents_fts (rowid, title, content, tags, metadata)
    VALUES (new.rowid, new.title, new.content, new.tags_json, new.metadata_json);
END;

CREATE TRIGGER IF NOT EXISTS retrieval_documents_ad AFTER DELETE ON retrieval_documents BEGIN
    INSERT INTO retrieval_documents_fts (retrieval_documents_fts, rowid, title, content, tags, metadata)
    VALUES ('delete', old.rowid, old.title, old.content, old.tags_json, old.metadata_json);
END;

CREATE TRIGGER IF NOT EXISTS retrieval_documents_au AFTER UPDATE ON retrieval_documents BEGIN
    INSERT INTO retrieval_documents_fts (retrieval_documents_fts, rowid, title, content, tags, metadata)
    VALUES ('delete', old.rowid, old.title, old.content, old.tags_json, old.metadata_json);
    INSERT INTO retrieval_documents_fts (rowid, title, content, tags, metadata)
    VALUES (new.rowid, new.title, new.content, new.tags_json, new.metadata_json);
END;
