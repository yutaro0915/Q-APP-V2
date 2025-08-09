'use client';

import { useState, FormEvent, ChangeEvent } from 'react';
import { Loader2 } from 'lucide-react';

interface ThreadTag {
  key: string;
  value: string;
}

interface ThreadFormData {
  title: string;
  body: string;
  tags: ThreadTag[];
  imageKey: string | null;
}

interface ThreadFormProps {
  onSubmit: (data: ThreadFormData) => Promise<void> | void;
  onCancel: () => void;
}

export function ThreadForm({ onSubmit, onCancel }: ThreadFormProps) {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [tags, setTags] = useState<Map<string, string>>(new Map());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Tag form states
  const [selectedType, setSelectedType] = useState('');
  const [location, setLocation] = useState('');
  const [deadline, setDeadline] = useState('');
  const [courseCode, setCourseCode] = useState('');

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    // Title validation
    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      newErrors.title = 'タイトルは必須です';
    } else if (trimmedTitle.length > 60) {
      newErrors.title = 'タイトルは60文字以内で入力してください';
    }
    
    // Body validation
    if (body.length > 2000) {
      newErrors.body = '本文は2000文字以内で入力してください';
    }
    
    // Deadline validation
    if (deadline && !isValidDateFormat(deadline)) {
      newErrors.deadline = '締切はYYYY-MM-DD形式で入力してください';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isValidDateFormat = (date: string): boolean => {
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    return dateRegex.test(date);
  };

  const updateTags = () => {
    const newTags = new Map<string, string>();
    
    if (selectedType) {
      newTags.set('種別', selectedType);
    }
    if (location.trim()) {
      newTags.set('場所', location.trim());
    }
    if (deadline && isValidDateFormat(deadline)) {
      newTags.set('締切', deadline);
    }
    if (courseCode.trim()) {
      newTags.set('授業コード', courseCode.trim());
    }
    
    setTags(newTags);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    setSubmitError(null);
    
    // Update tags before submission
    updateTags();
    
    const formData: ThreadFormData = {
      title: title.trim(),
      body: body.trim(),
      tags: Array.from(tags.entries()).map(([key, value]) => ({ key, value })),
      imageKey: null
    };
    
    try {
      await onSubmit(formData);
      // Reset form on success
      setTitle('');
      setBody('');
      setSelectedType('');
      setLocation('');
      setDeadline('');
      setCourseCode('');
      setTags(new Map());
      setErrors({});
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : '投稿に失敗しました');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTypeChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelectedType(value);
    
    const newTags = new Map(tags);
    if (value) {
      newTags.set('種別', value);
    } else {
      newTags.delete('種別');
    }
    setTags(newTags);
  };

  const handleLocationChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setLocation(value);
    
    const newTags = new Map(tags);
    if (value.trim()) {
      newTags.set('場所', value.trim());
    } else {
      newTags.delete('場所');
    }
    setTags(newTags);
  };

  const handleDeadlineChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setDeadline(value);
    
    const newTags = new Map(tags);
    if (value && isValidDateFormat(value)) {
      newTags.set('締切', value);
    } else {
      newTags.delete('締切');
    }
    setTags(newTags);
    
    // Clear deadline error if valid
    if (value && isValidDateFormat(value) && errors.deadline) {
      const newErrors = { ...errors };
      delete newErrors.deadline;
      setErrors(newErrors);
    }
  };

  const handleCourseCodeChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setCourseCode(value);
    
    const newTags = new Map(tags);
    if (value.trim()) {
      newTags.set('授業コード', value.trim());
    } else {
      newTags.delete('授業コード');
    }
    setTags(newTags);
  };

  const getTypeLabel = (value: string): string => {
    switch (value) {
      case 'question': return '質問';
      case 'notice': return '告知';
      case 'recruit': return '募集';
      case 'chat': return '雑談';
      default: return '';
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 bg-white rounded-lg shadow">
      {/* Title Field */}
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
          タイトル <span className="text-red-500">*</span>
        </label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.title ? 'border-red-500' : 'border-gray-300'
          }`}
          maxLength={60}
          disabled={isSubmitting}
        />
        <div className="mt-1 flex justify-between">
          <span className="text-xs text-gray-500">
            {title.trim().length} / 60
          </span>
          {errors.title && (
            <span className="text-xs text-red-500">{errors.title}</span>
          )}
        </div>
      </div>

      {/* Body Field */}
      <div>
        <label htmlFor="body" className="block text-sm font-medium text-gray-700 mb-1">
          本文
        </label>
        <textarea
          id="body"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={6}
          className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            errors.body ? 'border-red-500' : 'border-gray-300'
          }`}
          maxLength={2000}
          disabled={isSubmitting}
        />
        <div className="mt-1 flex justify-between">
          <span className="text-xs text-gray-500">
            {body.length} / 2000
          </span>
          {errors.body && (
            <span className="text-xs text-red-500">{errors.body}</span>
          )}
        </div>
      </div>

      {/* Tags Section */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">タグ</h3>
        
        <div className="space-y-3">
          {/* Type Tag */}
          <div>
            <label htmlFor="type" className="block text-xs text-gray-600 mb-1">
              種別
            </label>
            <select
              id="type"
              value={selectedType}
              onChange={handleTypeChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isSubmitting}
            >
              <option value="">選択してください</option>
              <option value="question">質問</option>
              <option value="notice">告知</option>
              <option value="recruit">募集</option>
              <option value="chat">雑談</option>
            </select>
          </div>

          {/* Location Tag */}
          <div>
            <label htmlFor="location" className="block text-xs text-gray-600 mb-1">
              場所
            </label>
            <input
              id="location"
              type="text"
              value={location}
              onChange={handleLocationChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              maxLength={50}
              placeholder="例: 伊都キャンパス"
              disabled={isSubmitting}
            />
          </div>

          {/* Deadline Tag */}
          <div>
            <label htmlFor="deadline" className="block text-xs text-gray-600 mb-1">
              締切
            </label>
            <input
              id="deadline"
              type="text"
              value={deadline}
              onChange={handleDeadlineChange}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.deadline ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="YYYY-MM-DD"
              disabled={isSubmitting}
            />
            {errors.deadline && (
              <span className="text-xs text-red-500">{errors.deadline}</span>
            )}
          </div>

          {/* Course Code Tag */}
          <div>
            <label htmlFor="courseCode" className="block text-xs text-gray-600 mb-1">
              授業コード
            </label>
            <input
              id="courseCode"
              type="text"
              value={courseCode}
              onChange={handleCourseCodeChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              maxLength={32}
              placeholder="例: CS101"
              disabled={isSubmitting}
            />
          </div>
        </div>

        {/* Display selected tags */}
        {tags.size > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {Array.from(tags.entries()).map(([key, value]) => (
              <span
                key={key}
                className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
              >
                {key === '種別' ? getTypeLabel(value) : value}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Error Message */}
      {submitError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{submitError}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 justify-end">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          disabled={isSubmitting}
        >
          キャンセル
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-white bg-blue-500 rounded-md hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              投稿中...
            </>
          ) : (
            '投稿する'
          )}
        </button>
      </div>
    </form>
  );
}