import {
  signInWithPopup,
  GoogleAuthProvider,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  type User
} from 'firebase/auth';
import { doc, setDoc, serverTimestamp } from 'firebase/firestore';
import { auth, db } from './config';

const googleProvider = new GoogleAuthProvider();

export const ADMIN_EMAIL = 'jsh8603@gmail.com';

export function isAdmin(user: User | null): boolean {
  return user?.email === ADMIN_EMAIL;
}

export async function signInWithGoogle() {
  if (!auth) throw new Error('Firebase not configured');
  const result = await signInWithPopup(auth, googleProvider);
  await saveUserToFirestore(result.user);
  return result.user;
}

export async function signInWithEmail(email: string, password: string) {
  if (!auth) throw new Error('Firebase not configured');
  const result = await signInWithEmailAndPassword(auth, email, password);
  await saveUserToFirestore(result.user);
  return result.user;
}

export async function signUpWithEmail(email: string, password: string) {
  if (!auth) throw new Error('Firebase not configured');
  const result = await createUserWithEmailAndPassword(auth, email, password);
  await saveUserToFirestore(result.user);
  return result.user;
}

export async function signOut() {
  if (!auth) throw new Error('Firebase not configured');
  return firebaseSignOut(auth);
}

async function saveUserToFirestore(user: User) {
  if (!db) return;
  const userRef = doc(db, 'users', user.uid);
  await setDoc(userRef, {
    uid: user.uid,
    email: user.email,
    displayName: user.displayName,
    photoUrl: user.photoURL,
    lastLoginAt: serverTimestamp(),
  }, { merge: true });
}
