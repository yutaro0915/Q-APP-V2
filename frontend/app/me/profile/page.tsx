'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  getMyProfile, 
  updateProfile, 
  FACULTY_OPTIONS, 
  MIN_YEAR, 
  MAX_YEAR,
  MyProfile,
  ProfileUpdateData 
} from '@/lib/actions/updateProfile';
import { ApiError, NetworkError } from '@/lib/api';

interface FormData {
  faculty: string | null;
  year: number | null;
  faculty_public: boolean;
  year_public: boolean;
}

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<MyProfile | null>(null);
  const [formData, setFormData] = useState<FormData>({
    faculty: null,
    year: null,
    faculty_public: false,
    year_public: false
  });
  const [originalData, setOriginalData] = useState<FormData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Load profile data
  useEffect(() => {
    async function loadProfile() {
      try {
        setLoading(true);
        setError(null);
        const profileData = await getMyProfile();
        setProfile(profileData);
        
        const formState: FormData = {
          faculty: profileData.faculty,
          year: profileData.year,
          faculty_public: profileData.faculty_public,
          year_public: profileData.year_public
        };
        
        setFormData(formState);
        setOriginalData(formState);
      } catch (err) {
        console.error('Failed to load profile:', err);
        if (err instanceof ApiError) {
          if (err.status === 401) {
            router.push('/');
            return;
          }
          setError(`プロフィールの取得に失敗しました: ${err.message}`);
        } else if (err instanceof NetworkError) {
          setError('ネットワークエラーが発生しました。インターネット接続を確認してください。');
        } else {
          setError('プロフィールの取得に失敗しました。');
        }
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, [router]);

  // Check if form has changes
  const hasChanges = originalData && (
    formData.faculty !== originalData.faculty ||
    formData.year !== originalData.year ||
    formData.faculty_public !== originalData.faculty_public ||
    formData.year_public !== originalData.year_public
  );

  // Form validation
  const validateForm = (): string | null => {
    if (formData.faculty && formData.faculty.length > 50) {
      return '学部名は50文字以内で入力してください';
    }
    if (formData.year && (formData.year < MIN_YEAR || formData.year > MAX_YEAR)) {
      return `学年は${MIN_YEAR}年から${MAX_YEAR}年の間で選択してください`;
    }
    return null;
  };

  // Handle form submission
  const handleSave = async () => {
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      // Only include changed fields
      const updateData: ProfileUpdateData = {};
      if (formData.faculty !== originalData?.faculty) {
        updateData.faculty = formData.faculty;
      }
      if (formData.year !== originalData?.year) {
        updateData.year = formData.year;
      }
      if (formData.faculty_public !== originalData?.faculty_public) {
        updateData.faculty_public = formData.faculty_public;
      }
      if (formData.year_public !== originalData?.year_public) {
        updateData.year_public = formData.year_public;
      }

      await updateProfile(updateData);
      
      // Update original data to reflect saved state
      setOriginalData({ ...formData });
      setSuccess(true);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to save profile:', err);
      if (err instanceof ApiError) {
        if (err.status === 401) {
          router.push('/');
          return;
        }
        setError(`保存に失敗しました: ${err.message}`);
      } else if (err instanceof NetworkError) {
        setError('ネットワークエラーが発生しました。インターネット接続を確認してください。');
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('保存に失敗しました。');
      }
    } finally {
      setSaving(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    if (originalData) {
      setFormData({ ...originalData });
      setError(null);
      setSuccess(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-md mx-auto px-4">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-center">読み込み中...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-md mx-auto px-4">
        <div className="bg-white rounded-lg shadow-sm">
          {/* Header */}
          <div className="px-6 py-4 border-b">
            <h1 className="text-lg font-semibold text-gray-900">プロフィール設定</h1>
          </div>

          {/* Form */}
          <div className="p-6 space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {success && (
              <div className="bg-green-50 border border-green-200 rounded-md p-3">
                <p className="text-sm text-green-700">プロフィールを保存しました</p>
              </div>
            )}

            {/* Faculty Selection */}
            <div>
              <label htmlFor="faculty" className="block text-sm font-medium text-gray-700 mb-2">
                学部
              </label>
              <select
                id="faculty"
                value={formData.faculty || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  faculty: e.target.value || null
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">選択してください</option>
                {FACULTY_OPTIONS.map(faculty => (
                  <option key={faculty} value={faculty}>{faculty}</option>
                ))}
              </select>
            </div>

            {/* Faculty Public Setting */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.faculty_public}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    faculty_public: e.target.checked
                  }))}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">学部を公開する</span>
              </label>
            </div>

            {/* Year Selection */}
            <div>
              <label htmlFor="year" className="block text-sm font-medium text-gray-700 mb-2">
                学年
              </label>
              <select
                id="year"
                value={formData.year || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  year: e.target.value ? parseInt(e.target.value) : null
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">選択してください</option>
                <option value="1">1年</option>
                <option value="2">2年</option>
                <option value="3">3年</option>
                <option value="4">4年</option>
                <option value="5">M1（修士1年）</option>
                <option value="6">M2（修士2年）</option>
                <option value="7">D1（博士1年）</option>
                <option value="8">D2（博士2年）</option>
                <option value="9">D3（博士3年）</option>
                <option value="10">その他</option>
              </select>
            </div>

            {/* Year Public Setting */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.year_public}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    year_public: e.target.checked
                  }))}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">学年を公開する</span>
              </label>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <button
                onClick={handleSave}
                disabled={!hasChanges || saving}
                className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  hasChanges && !saving
                    ? 'bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {saving ? '保存中...' : '保存'}
              </button>
              <button
                onClick={handleCancel}
                disabled={!hasChanges || saving}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  hasChanges && !saving
                    ? 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                キャンセル
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}