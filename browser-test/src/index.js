const EncryptedStorage = require('./storage');
const { v4: uuidv4 } = require('uuid');

function logOutput(message) {
    console.log(message);
    const outputDiv = document.getElementById('output');
    if (outputDiv) {
        outputDiv.innerHTML += message + '<br/>';
    }
}

async function runTest() {
    const outputDiv = document.getElementById('output');
    if (outputDiv) outputDiv.innerHTML = ''; // clear previous

    logOutput("テスト開始...");

    try {
        const storage = new EncryptedStorage();
        logOutput("storageインスタンス作成完了");

        logOutput("データベースの初期化中...");
        await storage.initializeDatabase("secure_passphrase123");
        logOutput("データベース初期化完了！");

        logOutput("データの保存中...");
        const schemaUuid = uuidv4();
        const payload = { message: "Hello from WebAssembly SQLite!", timestamp: Date.now() };
        const objectUuid = storage.storePayload(schemaUuid, "application/json", payload);
        logOutput(`データを保存しました。Object UUID: ${objectUuid}`);

        logOutput("データの取得中...");
        const retrievedPayload = storage.retrievePayload(objectUuid);
        logOutput("取得したデータ: " + JSON.stringify(retrievedPayload));

        if (retrievedPayload.message === payload.message) {
            logOutput("✅ テスト成功：データが正しく保存・取得されました！");
        } else {
            logOutput("❌ テスト失敗：データが一致しません。");
        }

        // Test Unlock
        logOutput("--- 一旦ロックして再解錠のテスト ---");
        storage.activeDbKek = null;
        storage.activeDbKid = null;
        logOutput("データベースをロックしました。");

        logOutput("パスフレーズで再解錠中...");
        await storage.unlockDatabase("secure_passphrase123");
        logOutput("再解錠成功！");

        const retrievedPayload2 = storage.retrievePayload(objectUuid);
        if (retrievedPayload2.message === payload.message) {
            logOutput("✅ 再解錠後のデータ取得テスト成功！");
        } else {
            logOutput("❌ 再解錠後のデータ取得失敗。");
        }

        storage.close();
        logOutput("データベースを閉じました。");

    } catch (err) {
        logOutput(`エラー発生: ${err.message}`);
        console.error(err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('runTestBtn');
    if (btn) {
        btn.addEventListener('click', runTest);
    }
});
