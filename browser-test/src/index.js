const EncryptedStorage = require('./storage');
const { v4: uuidv4 } = require('uuid');

const tablePages = {};
const ROWS_PER_PAGE = 10;
let currentStorage = null;

function logOutput(message) {
    console.log(message);
    const outputDiv = document.getElementById('output');
    if (outputDiv) {
        // DOMPurify could be used here in production, but for testing textContent inside a created element avoids XSS.
        const div = document.createElement('div');
        div.textContent = message;
        outputDiv.appendChild(div);
        outputDiv.scrollTop = outputDiv.scrollHeight;
    }
}

function renderTables(storage) {
    if (!storage || !storage.db) return;

    const tablesContainer = document.getElementById('tables-container');
    if (!tablesContainer) return;

    // Get all user tables
    let tables = [];
    try {
        const stmt = storage.db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'");
        while (stmt.step()) {
            tables.push(stmt.get()[0]);
        }
        stmt.free();
    } catch (e) {
        console.error("Failed to query tables", e);
        return;
    }

    tablesContainer.innerHTML = ''; // clear

    tables.forEach(tableName => {
        if (!tablePages[tableName]) {
            tablePages[tableName] = 1;
        }

        let totalRows = 0;
        try {
            const countStmt = storage.db.prepare(`SELECT COUNT(*) FROM "${tableName}"`);
            if (countStmt.step()) {
                totalRows = countStmt.get()[0];
            }
            countStmt.free();
        } catch (e) {
            console.error(`Failed to count rows for ${tableName}`, e);
        }

        const totalPages = Math.max(1, Math.ceil(totalRows / ROWS_PER_PAGE));
        if (tablePages[tableName] > totalPages) {
            tablePages[tableName] = totalPages;
        }

        const currentPage = tablePages[tableName];
        const offset = (currentPage - 1) * ROWS_PER_PAGE;

        let columns = [];
        let rows = [];
        try {
            const dataStmt = storage.db.prepare(`SELECT * FROM "${tableName}" LIMIT ${ROWS_PER_PAGE} OFFSET ${offset}`);
            columns = dataStmt.getColumnNames();
            while (dataStmt.step()) {
                rows.push(dataStmt.get());
            }
            dataStmt.free();
        } catch (e) {
             console.error(`Failed to fetch data for ${tableName}`, e);
        }

        // Format Uint8Array to hex
        const formattedRows = rows.map(row =>
            row.map(val => {
                if (val instanceof Uint8Array) {
                    return Array.from(val).map(b => b.toString(16).padStart(2, '0')).join('');
                }
                return val;
            })
        );

        const wrapper = document.createElement('div');
        wrapper.className = 'table-wrapper';

        const h3 = document.createElement('h3');
        h3.textContent = tableName;
        wrapper.appendChild(h3);

        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const trHead = document.createElement('tr');
        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            trHead.appendChild(th);
        });
        thead.appendChild(trHead);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        if (formattedRows.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = columns.length || 1;
            td.textContent = 'No data';
            td.style.textAlign = 'center';
            tr.appendChild(td);
            tbody.appendChild(tr);
        } else {
            formattedRows.forEach(rowData => {
                const tr = document.createElement('tr');
                rowData.forEach(cellData => {
                    const td = document.createElement('td');
                    td.textContent = cellData;
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
        }
        table.appendChild(tbody);
        wrapper.appendChild(table);

        const pagination = document.createElement('div');
        pagination.className = 'pagination';

        const prevBtn = document.createElement('button');
        prevBtn.textContent = '前へ';
        prevBtn.disabled = currentPage === 1;
        prevBtn.onclick = () => {
            tablePages[tableName] = currentPage - 1;
            renderTables(storage);
        };

        const nextBtn = document.createElement('button');
        nextBtn.textContent = '次へ';
        nextBtn.disabled = currentPage === totalPages;
        nextBtn.onclick = () => {
            tablePages[tableName] = currentPage + 1;
            renderTables(storage);
        };

        const pageInfo = document.createElement('span');
        pageInfo.textContent = `ページ ${currentPage} / ${totalPages} (全 ${totalRows} 行)`;

        pagination.appendChild(prevBtn);
        pagination.appendChild(pageInfo);
        pagination.appendChild(nextBtn);
        wrapper.appendChild(pagination);

        tablesContainer.appendChild(wrapper);
    });
}

// ユーティリティ: 遅延を入れることでリアルタイム更新を視覚的に分かりやすくする
const delay = ms => new Promise(r => setTimeout(r, ms));

async function runTest() {
    const runTestBtn = document.getElementById('runTestBtn');
    const closeDbBtn = document.getElementById('closeDbBtn');
    if (runTestBtn) runTestBtn.disabled = true;
    if (closeDbBtn) closeDbBtn.disabled = true;

    if (currentStorage) {
        try {
            currentStorage.close();
            currentStorage = null;
            logOutput("前回のデータベースを閉じました。");
        } catch (e) {
            console.error("Failed to close previous storage", e);
            logOutput("前回のデータベースを閉じられませんでした。「データベースを閉じる」ボタンから再試行してください。");
            if (runTestBtn) runTestBtn.disabled = false;
            if (closeDbBtn) closeDbBtn.disabled = false;
            return;
        }
    }

    const outputDiv = document.getElementById('output');
    if (outputDiv) outputDiv.innerHTML = ''; // clear previous
    const tablesContainer = document.getElementById('tables-container');
    if (tablesContainer) tablesContainer.innerHTML = '';

    logOutput("テスト開始...");

    let storage = null;

    try {
        storage = new EncryptedStorage();
        await storage.init(); // スキーマを生成して初期の空テーブルを表示するため手動でinitを呼ぶ
        currentStorage = storage;

        // --- モンキーパッチでクエリを監視して自動更新 ---
        const originalExec = storage.db.exec.bind(storage.db);
        const originalRun = storage.db.run.bind(storage.db);
        const originalPrepare = storage.db.prepare.bind(storage.db);
        let inTransaction = false;

        const updateIfNecessary = (sql) => {
            if (!sql) return;
            const upperSql = sql.toString().toUpperCase();
            if (upperSql.includes('BEGIN')) {
                inTransaction = true;
            } else if (upperSql.includes('COMMIT') || upperSql.includes('ROLLBACK')) {
                inTransaction = false;
                renderTables(storage);
            } else if (!inTransaction && (upperSql.includes('INSERT') || upperSql.includes('UPDATE') || upperSql.includes('DELETE'))) {
                renderTables(storage);
            }
        };

        storage.db.exec = function(sql) {
            const result = originalExec(sql);
            updateIfNecessary(sql);
            return result;
        };

        storage.db.run = function(sql, params) {
            const result = originalRun(sql, params);
            updateIfNecessary(sql);
            return result;
        };

        storage.db.prepare = function(sql, params) {
            const stmt = originalPrepare(sql, params);
            const originalStmtStep = stmt.step.bind(stmt);
            const originalStmtRun = stmt.run ? stmt.run.bind(stmt) : null;

            stmt.step = function() {
                const result = originalStmtStep();
                updateIfNecessary(sql);
                return result;
            };

            if (originalStmtRun) {
                stmt.run = function(values) {
                    const result = originalStmtRun(values);
                    updateIfNecessary(sql);
                    return result;
                };
            }
            return stmt;
        };
        // --- モンキーパッチ終了 ---

        // 初期状態の表示
        renderTables(storage);

        logOutput("storageインスタンス作成完了");
        await delay(1000);

        logOutput("データベースの初期化中...");
        await storage.initializeDatabase("secure_passphrase123");
        logOutput("データベース初期化完了！");
        await delay(1000);

        logOutput("データの保存中...");
        const schemaUuid = uuidv4();
        const payload = { message: "Hello from WebAssembly SQLite!", timestamp: Date.now() };
        const objectUuid = storage.storePayload(schemaUuid, "application/json", payload);
        logOutput(`データを保存しました。Object UUID: ${objectUuid}`);
        await delay(1000);

        logOutput("データの取得中...");
        const retrievedPayload = storage.retrievePayload(objectUuid);
        logOutput("取得したデータ: " + JSON.stringify(retrievedPayload));

        if (retrievedPayload.message === payload.message) {
            logOutput("✅ テスト成功：データが正しく保存・取得されました！");
        } else {
            logOutput("❌ テスト失敗：データが一致しません。");
        }
        await delay(1000);

        // Test Unlock
        logOutput("--- 一旦ロックして再解錠のテスト ---");
        storage.lock();
        logOutput("データベースをロックしました。");
        await delay(1000);

        logOutput("パスフレーズで再解錠中...");
        await storage.unlockDatabase("secure_passphrase123");
        logOutput("再解錠成功！");
        await delay(1000);

        const retrievedPayload2 = storage.retrievePayload(objectUuid);
        if (retrievedPayload2.message === payload.message) {
            logOutput("✅ 再解錠後のデータ取得テスト成功！");
        } else {
            logOutput("❌ 再解錠後のデータ取得失敗。");
        }

        logOutput("テスト完了！データベースは開いたままです。確認が終わったら「データベースを閉じる」ボタンを押してください。");
    } catch (err) {
        logOutput(`エラー発生: ${err.message}`);
        console.error(err);
        if (storage) {
            try {
                storage.close();
                if (currentStorage === storage) {
                    currentStorage = null;
                }
            } catch (closeErr) {
                console.error("Failed to close storage after test error", closeErr);
                currentStorage = storage;
                logOutput("テスト失敗後のデータベースを閉じられませんでした。「データベースを閉じる」ボタンから再試行してください。");
            }
        }
    } finally {
        if (runTestBtn) runTestBtn.disabled = false;
        if (closeDbBtn) closeDbBtn.disabled = !currentStorage;
    }
}

function closeDatabase() {
    const closeDbBtn = document.getElementById('closeDbBtn');

    if (currentStorage) {
        try {
            currentStorage.close();
            logOutput("データベースを手動で閉じました。（テーブルの表示はそのまま残しています）");
            currentStorage = null;
            if (closeDbBtn) closeDbBtn.disabled = true;
        } catch (e) {
            console.error("Failed to close storage", e);
            logOutput("データベースを閉じる際にエラーが発生しました。");
        }
    } else {
        logOutput("開いているデータベースはありません。");
        if (closeDbBtn) closeDbBtn.disabled = true;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('runTestBtn');
    if (btn) {
        btn.addEventListener('click', runTest);
    }
    const closeBtn = document.getElementById('closeDbBtn');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeDatabase);
    }
});
