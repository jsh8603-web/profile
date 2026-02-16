#!/usr/bin/env node
/**
 * upload_article.mjs - Firebase Storage 업로드 + Firestore 문서 생성
 *
 * Usage:
 *   node upload_article.mjs \
 *     --file "temp/slides.pdf" \
 *     --title "제목" \
 *     --type "disease" \
 *     --tags "관절,치료" \
 *     --summary "요약" \
 *     --content "본문" \
 *     --analyzedBy "Vision OCR"
 *
 * stdout: JSON { docId, url }
 */

import fs, { readFileSync } from "fs";
import { basename, resolve } from "path";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { createRequire } from "module";

const require = createRequire(import.meta.url);

// firebase-admin은 CommonJS이므로 require 사용
const admin = require("firebase-admin");

// ── Args 파싱 ──────────────────────────────────────────────
function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    if (argv[i].startsWith("--")) {
      const key = argv[i].slice(2);
      const val = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[i + 1] : "";
      args[key] = val;
      if (val) i++;
    }
  }
  return args;
}

const args = parseArgs(process.argv);

if (!args.file) {
  console.error("Error: --file is required");
  process.exit(1);
}

// ── Firebase 초기화 ────────────────────────────────────────
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = resolve(__dirname, "..", "..");

let serviceAccount;
let serviceAccountPath;

// 서비스 계정 검색 순서:
// 1. 환경 변수 (FIREBASE_SERVICE_ACCOUNT_PATH)
// 2. Downloads 폴더
// 3. 프로젝트 루트
const saEnv = process.env.FIREBASE_SERVICE_ACCOUNT_PATH;
const saDownloads = join(process.env.USERPROFILE || process.env.HOME, "Downloads", "miryangosweb-firebase-adminsdk-fbsvc-e139abbe14.json");
const saRoot = join(projectRoot, "firebase-service-account.json");

if (saEnv && fs.existsSync(saEnv)) {
  serviceAccountPath = saEnv;
} else if (fs.existsSync(saDownloads)) {
  serviceAccountPath = saDownloads;
} else if (fs.existsSync(saRoot)) {
  serviceAccountPath = saRoot;
}

if (!serviceAccountPath) {
  console.error("Error: Firebase service account file not found.");
  process.exit(1);
}

try {
  serviceAccount = JSON.parse(readFileSync(serviceAccountPath, "utf-8"));
  console.error(`Using service account: ${serviceAccountPath}`);
} catch (e) {
  console.error(`Error: Failed to parse service account at ${serviceAccountPath}`);
  process.exit(1);
}

if (!admin.apps.length) {
  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    storageBucket: `${serviceAccount.project_id}.firebasestorage.app`,
  });
}

const db = admin.firestore();
const bucket = admin.storage().bucket();

// ── 메인 로직 ──────────────────────────────────────────────
async function main() {
  const filePath = resolve(args.file);
  const fileName = basename(filePath);
  const title = args.title || fileName.replace(/\.[^/.]+$/, "");
  const type = args.type || "disease";
  const tags = args.tags ? args.tags.split(",").map((t) => t.trim()).filter(Boolean) : [];
  const summary = args.summary || "";
  const content = args.content || "";
  const analyzedBy = args.analyzedBy || "";

  // 1. Firebase Storage 업로드
  const timestamp = Date.now();
  const storagePath = `materials/${timestamp}_${fileName}`;

  let fileBuffer;
  try {
    fileBuffer = readFileSync(filePath);
  } catch (e) {
    console.error(`Error: Cannot read file ${filePath}`);
    process.exit(1);
  }

  const file = bucket.file(storagePath);
  await file.save(fileBuffer, {
    metadata: {
      contentType: fileName.endsWith(".pdf")
        ? "application/pdf"
        : "application/octet-stream",
    },
  });

  // 공개 URL 생성
  await file.makePublic();
  const publicUrl = `https://storage.googleapis.com/${bucket.name}/${storagePath}`;

  // 2. Firestore 문서 생성
  const docData = {
    title,
    type,
    tags,
    summary,
    content,
    attachmentUrl: publicUrl,
    attachmentName: fileName,
    pdfUrl: publicUrl,
    analyzedBy,
    isVisible: true,
    createdAt: admin.firestore.FieldValue.serverTimestamp(),
  };

  const docRef = await db.collection("articles").add(docData);

  // 3. 결과 출력
  const result = {
    docId: docRef.id,
    url: publicUrl,
    storagePath,
  };

  // stdout에 JSON만 출력 (Python에서 파싱)
  console.log(JSON.stringify(result));
}

main().catch((err) => {
  console.error(`Error: ${err.message}`);
  process.exit(1);
});
