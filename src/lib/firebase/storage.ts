import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';
import { requireStorage } from './config';

export async function uploadImage(file: File, path: string): Promise<string> {
  const storageRef = ref(requireStorage(), path);
  const snapshot = await uploadBytes(storageRef, file);
  return getDownloadURL(snapshot.ref);
}

export async function uploadPostImage(file: File, slug: string): Promise<string> {
  const ext = file.name.split('.').pop();
  const path = `posts/${slug}/${Date.now()}.${ext}`;
  return uploadImage(file, path);
}

export async function uploadPostFile(file: File, slug: string): Promise<string> {
  const ext = file.name.split('.').pop();
  const path = `posts/${slug}/${Date.now()}.${ext}`;
  return uploadImage(file, path);
}

export async function uploadProfileImage(file: File): Promise<string> {
  const ext = file.name.split('.').pop();
  const path = `profile/${Date.now()}.${ext}`;
  return uploadImage(file, path);
}
