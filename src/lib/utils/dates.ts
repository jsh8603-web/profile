import { Timestamp } from 'firebase/firestore';

export function formatDate(timestamp: Timestamp | Date | null): string {
  if (!timestamp) return '';
  const date = timestamp instanceof Timestamp ? timestamp.toDate() : timestamp;
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function formatDateShort(timestamp: Timestamp | Date | null): string {
  if (!timestamp) return '';
  const date = timestamp instanceof Timestamp ? timestamp.toDate() : timestamp;
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}
