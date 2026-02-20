import {
  collection,
  doc,
  getDoc,
  getDocs,
  addDoc,
  updateDoc,
  deleteDoc,
  setDoc,
  query,
  where,
  orderBy,
  limit,
  startAfter,
  serverTimestamp,
  increment,
  type DocumentData,
  type QueryDocumentSnapshot,
} from 'firebase/firestore';
import { requireDb } from './config';
import type { Post, Comment, Profile, SkillDetail } from '../types';

// ─── Posts ────────────────────────────────────────────
export async function getPosts(options?: {
  category?: string;
  publishedOnly?: boolean;
  pageSize?: number;
  lastDoc?: QueryDocumentSnapshot<DocumentData>;
}) {
  const db = requireDb();
  const { category, publishedOnly = true, pageSize = 9, lastDoc } = options || {};

  const q = collection(db, 'posts');
  const constraints: ReturnType<typeof where | typeof orderBy | typeof limit | typeof startAfter>[] = [];

  if (publishedOnly) constraints.push(where('published', '==', true));
  if (category) constraints.push(where('category', '==', category));
  constraints.push(orderBy('createdAt', 'desc'));
  if (pageSize) constraints.push(limit(pageSize));
  if (lastDoc) constraints.push(startAfter(lastDoc));

  const snapshot = await getDocs(query(q, ...constraints));
  const posts = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Post));
  const lastVisible = snapshot.docs[snapshot.docs.length - 1] || null;

  return { posts, lastVisible, hasMore: snapshot.docs.length === pageSize };
}

export async function getPostBySlug(slug: string): Promise<Post | null> {
  const db = requireDb();
  const q = query(collection(db, 'posts'), where('slug', '==', slug), limit(1));
  const snapshot = await getDocs(q);
  if (snapshot.empty) return null;
  const d = snapshot.docs[0];
  return { id: d.id, ...d.data() } as Post;
}

export async function getPostById(id: string): Promise<Post | null> {
  const db = requireDb();
  const docRef = doc(db, 'posts', id);
  const snapshot = await getDoc(docRef);
  if (!snapshot.exists()) return null;
  return { id: snapshot.id, ...snapshot.data() } as Post;
}

export async function createPost(data: Omit<Post, 'id' | 'createdAt' | 'updatedAt' | 'commentCount' | 'viewCount'>) {
  const db = requireDb();
  const docRef = await addDoc(collection(db, 'posts'), {
    ...data,
    commentCount: 0,
    viewCount: 0,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
    publishedAt: data.published ? serverTimestamp() : null,
  });
  return docRef.id;
}

export async function updatePost(id: string, data: Partial<Post>) {
  const db = requireDb();
  const docRef = doc(db, 'posts', id);
  await updateDoc(docRef, {
    ...data,
    updatedAt: serverTimestamp(),
  });
}

export async function deletePost(id: string) {
  const db = requireDb();
  await deleteDoc(doc(db, 'posts', id));
}

export async function incrementViewCount(postId: string) {
  const db = requireDb();
  const docRef = doc(db, 'posts', postId);
  await updateDoc(docRef, { viewCount: increment(1) });
}

// ─── Comments ─────────────────────────────────────────
export async function getComments(postId: string) {
  const db = requireDb();
  const q = query(
    collection(db, 'posts', postId, 'comments'),
    orderBy('createdAt', 'desc')
  );
  const snapshot = await getDocs(q);
  return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Comment));
}

export async function addComment(postId: string, data: Omit<Comment, 'id' | 'createdAt'>) {
  const db = requireDb();
  const commentRef = await addDoc(collection(db, 'posts', postId, 'comments'), {
    ...data,
    createdAt: serverTimestamp(),
  });
  await updateDoc(doc(db, 'posts', postId), { commentCount: increment(1) });
  return commentRef.id;
}

export async function deleteComment(postId: string, commentId: string) {
  const db = requireDb();
  await deleteDoc(doc(db, 'posts', postId, 'comments', commentId));
  await updateDoc(doc(db, 'posts', postId), { commentCount: increment(-1) });
}

// ─── Profile ──────────────────────────────────────────
export async function getProfile(): Promise<Profile | null> {
  const db = requireDb();
  const docRef = doc(db, 'profile', 'main');
  const snapshot = await getDoc(docRef);
  if (!snapshot.exists()) return null;
  return snapshot.data() as Profile;
}

export async function updateProfile(data: Partial<Profile>) {
  const db = requireDb();
  const docRef = doc(db, 'profile', 'main');
  await updateDoc(docRef, data);
}

// ─── Skills ──────────────────────────────────────────
export async function getSkill(slug: string): Promise<SkillDetail | null> {
  const db = requireDb();
  const docRef = doc(db, 'skills', slug);
  const snapshot = await getDoc(docRef);
  if (!snapshot.exists()) return null;
  return snapshot.data() as SkillDetail;
}

export async function getSkills(): Promise<SkillDetail[]> {
  const db = requireDb();
  const snapshot = await getDocs(collection(db, 'skills'));
  return snapshot.docs.map(d => d.data() as SkillDetail);
}

export async function setSkill(slug: string, data: SkillDetail) {
  const db = requireDb();
  const docRef = doc(db, 'skills', slug);
  await setDoc(docRef, data);
}

// ─── Admin Stats ──────────────────────────────────────
export async function getAdminStats() {
  const db = requireDb();
  const postsSnap = await getDocs(collection(db, 'posts'));
  const publishedCount = postsSnap.docs.filter(d => d.data().published).length;
  let totalComments = 0;
  let totalViews = 0;
  postsSnap.docs.forEach(d => {
    totalComments += d.data().commentCount || 0;
    totalViews += d.data().viewCount || 0;
  });
  return {
    totalPosts: postsSnap.size,
    publishedPosts: publishedCount,
    draftPosts: postsSnap.size - publishedCount,
    totalComments,
    totalViews,
  };
}
