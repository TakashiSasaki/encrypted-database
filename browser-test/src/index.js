const EncryptedStorage = require('./storage');
const { v4: uuidv4 } = require('uuid');

const tablePages = {};
const ROWS_PER_PAGE = 10;
let currentStorage = null;

function initializeTabs() {
    const container = document.getElementById('tables-container');
    if (!container) return;

    const tabButtons = container.querySelectorAll('.tab-button');
    const tabContents = container.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            const targetId = event.currentTarget.getAttribute('data-tab-target');

            tabContents.forEach(content => content.classList.remove('active'));
            tabButtons.forEach(btn => btn.classList.remove('active'));

            const targetContent = container.querySelector(`#${targetId}`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
            event.currentTarget.classList.add('active');
        });
    });
}

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

    const setupTablesContainer = document.getElementById('setup-tables');
    const dynamicTablesContainer = document.getElementById('dynamic-tables');
    if (!setupTablesContainer || !dynamicTablesContainer) return;

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

    setupTablesContainer.innerHTML = ''; // clear
    dynamicTablesContainer.innerHTML = ''; // clear

    const setupTableNames = [
        'key_class_tbl',
        'key_profile_tbl',
        'unlock_method_tbl',
        'unlock_provider_tbl',
        'platform_tbl',
        'unlock_provider_platform_tbl'
    ];

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

        if (setupTableNames.includes(tableName)) {
            setupTablesContainer.appendChild(wrapper);
        } else {
            dynamicTablesContainer.appendChild(wrapper);
        }
    });
}

// ステップ管理
let currentStepIndex = 0;
let testState = {
    schemaUuid: null,
    payload: null,
    objectUuid: null,
    passphrase: "secure_passphrase123"
};

const steps = [
    async () => {
        logOutput("ステップ 1: storageインスタンスの作成中...");
        const storage = new EncryptedStorage();
        await storage.init();
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

        renderTables(storage);
        logOutput("storageインスタンス作成完了");
    },
    async () => {
        logOutput("ステップ 2: データベースの初期化中...");
        await currentStorage.initializeDatabase(testState.passphrase);
        logOutput("データベース初期化完了！");
    },
    async () => {
        logOutput("ステップ 3: データの保存中...");
        testState.schemaUuid = uuidv4();
        testState.payload = { message: "Hello from WebAssembly SQLite!", timestamp: Date.now() };
        testState.objectUuid = currentStorage.storePayload(testState.schemaUuid, "application/json", testState.payload);
        logOutput(`データを保存しました。Object UUID: ${testState.objectUuid}`);
    },
    async () => {
        logOutput("ステップ 4: データの取得と検証中...");
        const retrievedPayload = currentStorage.retrievePayload(testState.objectUuid);
        logOutput("取得したデータ: " + JSON.stringify(retrievedPayload));

        if (retrievedPayload.message === testState.payload.message) {
            logOutput("✅ データの取得と検証成功！");
        } else {
            throw new Error("取得したデータが一致しません。");
        }
    },
    async () => {
        logOutput("ステップ 5: データベースのロック中...");
        currentStorage.lock();
        logOutput("データベースをロックしました。");
    },
    async () => {
        logOutput("ステップ 6: パスフレーズで再解錠中...");
        await currentStorage.unlockDatabase(testState.passphrase);
        logOutput("再解錠成功！");
    },
    async () => {
        logOutput("ステップ 7: 再解錠後のデータ取得検証中...");
        const retrievedPayload2 = currentStorage.retrievePayload(testState.objectUuid);
        if (retrievedPayload2.message === testState.payload.message) {
            logOutput("✅ 再解錠後のデータ取得テスト成功！");
            logOutput("テスト完了！データベースは開いたままです。確認が終わったら「データベースを閉じる」ボタンを押してください。");
        } else {
            throw new Error("再解錠後のデータ取得失敗。");
        }
    }
];

function updateStepUI(index, status) {
    const li = document.getElementById(`step-${index}`);
    if (!li) return;
    li.classList.remove('pending', 'active', 'completed', 'error');
    li.classList.add(status);

    const originalText = li.textContent.replace(/^\[.*?\]\s*/, '');
    let prefix = '[-]';
    if (status === 'active') prefix = '[▶]';
    if (status === 'completed') prefix = '[✓]';
    if (status === 'error') prefix = '[✕]';

    li.textContent = `${prefix} ${originalText}`;
}

async function executeNextStep() {
    const nextStepBtn = document.getElementById('nextStepBtn');
    const resetTestBtn = document.getElementById('resetTestBtn');
    const closeDbBtn = document.getElementById('closeDbBtn');

    if (nextStepBtn) nextStepBtn.disabled = true;

    if (currentStepIndex === 0) {
        // Clear previous state if starting fresh
        const outputDiv = document.getElementById('output');
        if (outputDiv) outputDiv.innerHTML = '';
        const setupTablesContainer = document.getElementById('setup-tables');
        if (setupTablesContainer) setupTablesContainer.innerHTML = '';
        const dynamicTablesContainer = document.getElementById('dynamic-tables');
        if (dynamicTablesContainer) dynamicTablesContainer.innerHTML = '';

        // Reset all steps to pending
        steps.forEach((_, idx) => updateStepUI(idx, 'pending'));

        if (resetTestBtn) resetTestBtn.style.display = 'inline-block';
    }

    try {
        updateStepUI(currentStepIndex, 'active');

        // Execute the step
        await steps[currentStepIndex]();

        updateStepUI(currentStepIndex, 'completed');
        currentStepIndex++;

        if (currentStepIndex < steps.length) {
            if (nextStepBtn) {
                nextStepBtn.textContent = '次のステップへ';
                nextStepBtn.disabled = false;
            }
        } else {
            if (nextStepBtn) {
                nextStepBtn.textContent = '全ステップ完了';
                nextStepBtn.disabled = true;
            }
        }
    } catch (err) {
        updateStepUI(currentStepIndex, 'error');
        logOutput(`エラー発生: ${err.message}`);
        console.error(err);
        if (nextStepBtn) nextStepBtn.disabled = true;
    } finally {
        if (closeDbBtn) closeDbBtn.disabled = !currentStorage;
    }
}

async function resetTest() {
    const nextStepBtn = document.getElementById('nextStepBtn');
    const resetTestBtn = document.getElementById('resetTestBtn');
    const closeDbBtn = document.getElementById('closeDbBtn');

    if (currentStorage) {
        try {
            currentStorage.close();
            currentStorage = null;
            logOutput("データベースを閉じました。");
        } catch (e) {
            console.error("Failed to close previous storage", e);
            logOutput("データベースを閉じられませんでした。");
        }
    }

    currentStepIndex = 0;
    testState = {
        schemaUuid: null,
        payload: null,
        objectUuid: null,
        passphrase: "secure_passphrase123"
    };

    steps.forEach((_, idx) => updateStepUI(idx, 'pending'));

    const outputDiv = document.getElementById('output');
    if (outputDiv) outputDiv.innerHTML = '';
    const setupTablesContainer = document.getElementById('setup-tables');
    if (setupTablesContainer) setupTablesContainer.innerHTML = '';
    const dynamicTablesContainer = document.getElementById('dynamic-tables');
    if (dynamicTablesContainer) dynamicTablesContainer.innerHTML = '';

    if (nextStepBtn) {
        nextStepBtn.textContent = 'テスト開始 / 次のステップへ';
        nextStepBtn.disabled = false;
    }
    if (resetTestBtn) resetTestBtn.style.display = 'none';
    if (closeDbBtn) closeDbBtn.disabled = true;
}

function closeDatabase() {
    const closeDbBtn = document.getElementById('closeDbBtn');
    const nextStepBtn = document.getElementById('nextStepBtn');
    const resetTestBtn = document.getElementById('resetTestBtn');

    if (currentStorage) {
        try {
            currentStorage.close();
            logOutput("データベースを手動で閉じました。（テーブルの表示はそのまま残しています）");
            currentStorage = null;
            if (closeDbBtn) closeDbBtn.disabled = true;

            // Disable next step button as the database is closed
            if (nextStepBtn) nextStepBtn.disabled = true;
            if (resetTestBtn) resetTestBtn.style.display = 'inline-block';
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
    initializeTabs();

    const btn = document.getElementById('nextStepBtn');
    if (btn) {
        btn.addEventListener('click', executeNextStep);
    }
    const resetBtn = document.getElementById('resetTestBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetTest);
    }
    const closeBtn = document.getElementById('closeDbBtn');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeDatabase);
    }
});
