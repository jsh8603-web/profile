/**
 * Upload slides PDFs + cover images to Firebase Storage & create Firestore documents.
 *
 * Usage:
 *   node scripts/upload-slides.mjs
 *
 * Requires:
 *   - FIREBASE_ADMIN_PASSWORD env var (admin user password)
 *   - .env.local with Firebase config (NEXT_PUBLIC_FIREBASE_*)
 */

import { readFileSync } from 'fs';
import { resolve } from 'path';
import { initializeApp } from 'firebase/app';
import { getAuth, signInWithEmailAndPassword } from 'firebase/auth';
import { getStorage, ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import {
  getFirestore,
  collection,
  addDoc,
  getDocs,
  deleteDoc,
  serverTimestamp,
  query,
  where,
} from 'firebase/firestore';

// ── Load .env.local ──
const envPath = resolve(process.cwd(), '.env.local');
const envContent = readFileSync(envPath, 'utf-8');
const env = {};
for (const line of envContent.split('\n')) {
  const match = line.match(/^([^#=]+)=(.*)$/);
  if (match) env[match[1].trim()] = match[2].trim();
}

const firebaseConfig = {
  apiKey: env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

const ADMIN_EMAIL = 'jsh8603@gmail.com';
const ADMIN_PASSWORD = process.env.FIREBASE_ADMIN_PASSWORD;

if (!ADMIN_PASSWORD) {
  console.error('Set FIREBASE_ADMIN_PASSWORD env var first.');
  console.error('  export FIREBASE_ADMIN_PASSWORD="your-password"');
  process.exit(1);
}

// ── Slides data ──
const SLIDES_BASE = 'D:/projects/slides-grab/slides';

const SLIDES = [
  { slug: 'ai-infra-investment', title: '2025 글로벌 AI 인프라 투자 전략', category: 'investment', cover: 'html-preview/slide-01.png' },
  { slug: 'samsung-investment-report', title: '삼성전자 투자전략 보고서 2025', category: 'investment', cover: 'preview/slide_01.png' },
  { slug: 'coupang-investment-report', title: 'Coupang Investment Report', category: 'investment', cover: 'assets/slide-01-cover-strategy.png' },
  { slug: 'kakao-investment-strategy', title: 'Kakao Investment Strategy Report', category: 'investment', cover: 'html-preview/slide-01.png' },
  { slug: 'lg-hynix-investment-strategy', title: 'SK Hynix Investment Strategy', category: 'investment', cover: 'preview/slide_01.png' },
  { slug: 'naver-investment-strategy', title: 'Naver Investment Strategy', category: 'investment', cover: 'html-preview/slide-01.png' },
  { slug: 'apartment-market-2026', title: '2026 한국 아파트 시장 분석', category: 'analysis', cover: 'assets/slide-01-cover-2026.png' },
  { slug: 'discounted-breakeven-analysis', title: 'Discounted Breakeven Analysis', category: 'analysis', cover: 'html-preview/slide-01.png' },
  { slug: 'manufacturing-kpi-report', title: 'Manufacturing KPI Report', category: 'operations', cover: 'assets/slide-01-image.png' },
  { slug: 'payroll-guide', title: 'Payroll Management Report 2025', category: 'operations', cover: 'assets/slide-01-cover.png' },
];

// ── Init Firebase ──
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const storage = getStorage(app);
const db = getFirestore(app);

async function uploadFile(localPath, storagePath, contentType) {
  const data = readFileSync(localPath);
  const storageRef = ref(storage, storagePath);
  await uploadBytes(storageRef, data, { contentType });
  return getDownloadURL(storageRef);
}

async function deleteExistingPosts() {
  console.log('\n🗑  Deleting existing posts...');
  const snapshot = await getDocs(collection(db, 'posts'));
  for (const doc of snapshot.docs) {
    await deleteDoc(doc.ref);
    console.log(`   Deleted: ${doc.data().title || doc.id}`);
  }
  console.log(`   Deleted ${snapshot.size} posts total.`);
}

async function main() {
  // Sign in
  console.log('🔐 Signing in...');
  await signInWithEmailAndPassword(auth, ADMIN_EMAIL, ADMIN_PASSWORD);
  console.log('✅ Authenticated as', ADMIN_EMAIL);

  // Delete existing posts
  await deleteExistingPosts();

  // Upload each slide
  console.log('\n📤 Uploading slides...');
  for (const slide of SLIDES) {
    const pdfPath = `${SLIDES_BASE}/${slide.slug}/${slide.slug}.pdf`;
    const coverPath = `${SLIDES_BASE}/${slide.slug}/${slide.cover}`;

    console.log(`\n── ${slide.title} ──`);

    // Check if already exists
    const existing = await getDocs(
      query(collection(db, 'posts'), where('slug', '==', slide.slug))
    );
    if (!existing.empty) {
      console.log('   ⏭  Already exists, skipping.');
      continue;
    }

    // Upload PDF
    console.log('   Uploading PDF...');
    const pdfUrl = await uploadFile(
      pdfPath,
      `posts/${slide.slug}/${slide.slug}.pdf`,
      'application/pdf'
    );

    // Upload cover image
    console.log('   Uploading cover...');
    const coverUrl = await uploadFile(
      coverPath,
      `posts/${slide.slug}/cover.png`,
      'image/png'
    );

    // Create Firestore document
    console.log('   Creating Firestore doc...');
    const docId = await addDoc(collection(db, 'posts'), {
      slug: slide.slug,
      title: slide.title,
      excerpt: '',
      content: '',
      category: slide.category,
      tags: [],
      coverImageUrl: coverUrl,
      published: true,
      authorName: 'Sehoon Jang',
      commentCount: 0,
      viewCount: 0,
      attachmentUrl: pdfUrl,
      attachmentName: `${slide.slug}.pdf`,
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
      publishedAt: serverTimestamp(),
    });

    console.log(`   ✅ Created: ${docId}`);
  }

  console.log('\n🎉 All slides uploaded successfully!');
  process.exit(0);
}

main().catch((err) => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
