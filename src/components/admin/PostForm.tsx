'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Eye, Edit as EditIcon, Upload, FileText, X } from 'lucide-react';
import { Button, Input, Badge } from '@/components/ui';
import { createPost, updatePost } from '@/lib/firebase/firestore';
import { uploadPostImage, uploadPostFile } from '@/lib/firebase/storage';
import { slugify } from '@/lib/utils/slugify';
import type { Post } from '@/lib/types';

interface PostFormProps {
  post?: Post;
  mode: 'create' | 'edit';
}

export default function PostForm({ post, mode }: PostFormProps) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pdfInputRef = useRef<HTMLInputElement>(null);
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState(false);
  const [tagInput, setTagInput] = useState('');

  const [form, setForm] = useState({
    title: post?.title || '',
    slug: post?.slug || '',
    excerpt: post?.excerpt || '',
    content: post?.content || '',
    category: post?.category || 'finance' as 'finance' | 'economy',
    tags: post?.tags || [] as string[],
    coverImageUrl: post?.coverImageUrl || '',
    published: post?.published || false,
    attachmentUrl: post?.attachmentUrl || '',
    attachmentName: post?.attachmentName || '',
  });

  const updateField = (field: keyof typeof form, value: typeof form[keyof typeof form]) => {
    setForm(prev => ({ ...prev, [field]: value }));
    if (field === 'title' && mode === 'create') {
      setForm(prev => ({ ...prev, slug: slugify(value as string) }));
    }
  };

  const addTag = () => {
    const tag = tagInput.trim();
    if (tag && !form.tags.includes(tag)) {
      setForm(prev => ({ ...prev, tags: [...prev.tags, tag] }));
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setForm(prev => ({ ...prev, tags: prev.tags.filter(t => t !== tag) }));
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      alert('Image must be under 5MB');
      return;
    }
    try {
      const url = await uploadPostImage(file, form.slug || 'temp');
      updateField('coverImageUrl', url);
    } catch (err) {
      console.error('Upload failed:', err);
      alert('Image upload failed');
    }
  };

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 20 * 1024 * 1024) {
      alert('PDF must be under 20MB');
      return;
    }
    try {
      const url = await uploadPostFile(file, form.slug || 'temp');
      setForm(prev => ({ ...prev, attachmentUrl: url, attachmentName: file.name }));
    } catch (err) {
      console.error('PDF upload failed:', err);
      alert('PDF upload failed');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title || !form.content) {
      alert('Title and content are required');
      return;
    }
    setSaving(true);
    try {
      if (mode === 'create') {
        await createPost({
          ...form,
          authorName: 'Sehoon Jang',
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          publishedAt: form.published ? new Date() as any : null,
        });
      } else if (post) {
        await updatePost(post.id, {
          ...form,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          publishedAt: form.published && !post.published ? new Date() as any : post.publishedAt,
        });
      }
      router.push('/admin/posts');
    } catch (err) {
      console.error('Save failed:', err);
      alert('Failed to save post');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-4xl">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-[#1D1D1F]">
          {mode === 'create' ? 'New Post' : 'Edit Post'}
        </h1>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            onClick={() => setPreview(!preview)}
          >
            {preview ? <EditIcon size={16} /> : <Eye size={16} />}
            {preview ? 'Edit' : 'Preview'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() => { updateField('published', false); }}
            disabled={saving}
          >
            Save Draft
          </Button>
          <Button
            type="submit"
            onClick={() => updateField('published', true)}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Publish'}
          </Button>
        </div>
      </div>

      <div className="space-y-6">
        {/* Title */}
        <div>
          <Input
            label="Title"
            id="title"
            value={form.title}
            onChange={(e) => updateField('title', e.target.value)}
            placeholder="Post title..."
            required
          />
        </div>

        {/* Slug */}
        <div>
          <Input
            label="Slug"
            id="slug"
            value={form.slug}
            onChange={(e) => updateField('slug', e.target.value)}
            placeholder="post-url-slug"
          />
        </div>

        {/* Excerpt */}
        <div>
          <label className="block text-sm font-medium text-[#1D1D1F] mb-1.5">Excerpt</label>
          <textarea
            value={form.excerpt}
            onChange={(e) => updateField('excerpt', e.target.value)}
            placeholder="Brief description..."
            rows={2}
            className="w-full px-4 py-2.5 rounded-xl border border-[#D2D2D7] bg-white text-sm text-[#1D1D1F] placeholder:text-[#86868B] focus:outline-none focus:ring-2 focus:ring-[#0071E3]/30 focus:border-[#0071E3] transition-all resize-none"
          />
        </div>

        {/* Category */}
        <div>
          <label className="block text-sm font-medium text-[#1D1D1F] mb-1.5">Category</label>
          <div className="flex gap-2">
            {(['finance', 'economy'] as const).map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => updateField('category', cat)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  form.category === cat
                    ? 'bg-[#0071E3] text-white'
                    : 'bg-[#F5F5F7] text-[#424245] hover:bg-[#E8E8ED]'
                }`}
              >
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm font-medium text-[#1D1D1F] mb-1.5">Tags</label>
          <div className="flex flex-wrap gap-2 mb-2">
            {form.tags.map((tag) => (
              <Badge key={tag} variant="outline">
                {tag}
                <button type="button" onClick={() => removeTag(tag)} className="ml-1 text-red-400 hover:text-red-600">×</button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addTag(); } }}
              placeholder="Add tag..."
              className="flex-1 px-4 py-2 rounded-xl border border-[#D2D2D7] bg-white text-sm"
            />
            <Button type="button" variant="secondary" size="sm" onClick={addTag}>Add</Button>
          </div>
        </div>

        {/* Cover Image */}
        <div>
          <label className="block text-sm font-medium text-[#1D1D1F] mb-1.5">Cover Image</label>
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-dashed border-[#D2D2D7] text-sm text-[#86868B] hover:border-[#0071E3] hover:text-[#0071E3] transition-colors"
            >
              <Upload size={16} />
              Upload Image
            </button>
            {form.coverImageUrl && (
              <span className="text-xs text-[#86868B] truncate max-w-xs">
                {form.coverImageUrl.split('/').pop()?.split('?')[0]}
              </span>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />
        </div>

        {/* PDF Attachment */}
        <div>
          <label className="block text-sm font-medium text-[#1D1D1F] mb-1.5">PDF Attachment</label>
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => pdfInputRef.current?.click()}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-dashed border-[#D2D2D7] text-sm text-[#86868B] hover:border-[#0071E3] hover:text-[#0071E3] transition-colors"
            >
              <FileText size={16} />
              Upload PDF
            </button>
            {form.attachmentName && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-[#86868B] truncate max-w-xs">
                  {form.attachmentName}
                </span>
                <button
                  type="button"
                  onClick={() => setForm(prev => ({ ...prev, attachmentUrl: '', attachmentName: '' }))}
                  className="text-red-400 hover:text-red-600"
                >
                  <X size={14} />
                </button>
              </div>
            )}
          </div>
          <input
            ref={pdfInputRef}
            type="file"
            accept=".pdf"
            onChange={handlePdfUpload}
            className="hidden"
          />
        </div>

        {/* Content Editor */}
        <div>
          <label className="block text-sm font-medium text-[#1D1D1F] mb-1.5">Content (Markdown)</label>
          {preview ? (
            <div className="prose prose-sm max-w-none p-6 rounded-xl border border-[#E8E8ED] bg-white min-h-[400px]">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{form.content}</ReactMarkdown>
            </div>
          ) : (
            <textarea
              value={form.content}
              onChange={(e) => updateField('content', e.target.value)}
              placeholder="Write your post in Markdown..."
              rows={20}
              className="w-full px-4 py-3 rounded-xl border border-[#D2D2D7] bg-white text-sm text-[#1D1D1F] font-mono placeholder:text-[#86868B] focus:outline-none focus:ring-2 focus:ring-[#0071E3]/30 focus:border-[#0071E3] transition-all resize-y min-h-[400px]"
            />
          )}
        </div>
      </div>
    </form>
  );
}
