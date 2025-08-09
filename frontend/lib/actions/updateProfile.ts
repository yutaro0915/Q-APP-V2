/**
 * Update profile actions
 * Client-side helper functions for profile management
 */

import { get, patch, ApiError, NetworkError } from '@/lib/api';

// Profile data types (matching backend DTOs)
export interface MyProfile {
  id: string;
  faculty: string | null;
  year: number | null;
  faculty_public: boolean;
  year_public: boolean;
  created_at: string | null;
}

export interface PublicProfile {
  id: string;
  faculty: string | null;
  year: number | null;
  created_at: string | null;
}

export interface ProfileUpdateData {
  faculty?: string | null;
  year?: number | null;
  faculty_public?: boolean;
  year_public?: boolean;
}

// Faculty enum for validation
export const FACULTY_OPTIONS = [
  '文学部',
  '教育学部', 
  '法学部',
  '経済学部',
  '理学部',
  '医学部',
  '歯学部',
  '薬学部',
  '工学部',
  '芸術工学部',
  '農学部',
  '共創学部',
] as const;

export type Faculty = typeof FACULTY_OPTIONS[number];

// Year validation constants
export const MIN_YEAR = 1;
export const MAX_YEAR = 10;

/**
 * Validate profile update data
 */
function validateProfileData(data: ProfileUpdateData): void {
  // Faculty validation
  if (data.faculty !== undefined && data.faculty !== null) {
    if (typeof data.faculty !== 'string') {
      throw new Error('学部は文字列で指定してください');
    }
    if (data.faculty.trim().length === 0) {
      throw new Error('学部が空です');
    }
    if (data.faculty.length > 50) {
      throw new Error('学部名は50文字以内で入力してください');
    }
  }

  // Year validation
  if (data.year !== undefined && data.year !== null) {
    if (typeof data.year !== 'number' || !Number.isInteger(data.year)) {
      throw new Error('学年は整数で指定してください');
    }
    if (data.year < MIN_YEAR || data.year > MAX_YEAR) {
      throw new Error(`学年は${MIN_YEAR}年から${MAX_YEAR}年の間で指定してください`);
    }
  }

  // Public flags validation
  if (data.faculty_public !== undefined && typeof data.faculty_public !== 'boolean') {
    throw new Error('学部公開設定はboolean値で指定してください');
  }
  if (data.year_public !== undefined && typeof data.year_public !== 'boolean') {
    throw new Error('学年公開設定はboolean値で指定してください');
  }
}

/**
 * Get my profile data
 * @returns My profile with all fields
 * @throws {Error} Authentication error
 * @throws {ApiError} API error response  
 * @throws {NetworkError} Network error
 */
export async function getMyProfile(): Promise<MyProfile> {
  // Get auth token from localStorage
  const token = localStorage.getItem('auth_token');
  if (!token) {
    throw new Error('認証が必要です');
  }

  try {
    // Call API
    const profile = await get<MyProfile>('/auth/me/profile', {
      token,
    });

    return profile;
  } catch (error) {
    // Re-throw API and Network errors as-is
    if (error instanceof ApiError || error instanceof NetworkError) {
      throw error;
    }
    
    // Wrap other errors
    throw new Error('プロフィールの取得に失敗しました');
  }
}

/**
 * Update my profile
 * @param data Profile update data
 * @throws {Error} Validation or authentication error
 * @throws {ApiError} API error response
 * @throws {NetworkError} Network error
 */
export async function updateProfile(data: ProfileUpdateData): Promise<void> {
  // Get auth token from localStorage
  const token = localStorage.getItem('auth_token');
  if (!token) {
    throw new Error('認証が必要です');
  }

  // Validate input data
  validateProfileData(data);

  // Prepare request data, only include non-undefined fields
  const requestData: ProfileUpdateData = {};
  if (data.faculty !== undefined) {
    requestData.faculty = data.faculty?.trim() || null;
  }
  if (data.year !== undefined) {
    requestData.year = data.year;
  }
  if (data.faculty_public !== undefined) {
    requestData.faculty_public = data.faculty_public;
  }
  if (data.year_public !== undefined) {
    requestData.year_public = data.year_public;
  }

  try {
    // Call API - PATCH returns 204 No Content
    await patch<void>('/auth/me/profile', requestData, {
      token,
    });
  } catch (error) {
    // Re-throw API and Network errors as-is
    if (error instanceof ApiError) {
      // Add more specific error messages based on API error codes
      if (error.code === 'VALIDATION_ERROR') {
        throw new Error('入力データが正しくありません: ' + error.message);
      }
      throw error;
    }
    if (error instanceof NetworkError) {
      throw error;
    }
    
    // Wrap other errors
    throw new Error('プロフィールの更新に失敗しました');
  }
}

/**
 * Helper function to get display text for year
 */
export function getYearDisplayText(year: number | null): string {
  if (year === null) {
    return '未設定';
  }
  if (year >= 1 && year <= 4) {
    return `${year}年`;
  }
  if (year === 5) {
    return 'M1';
  }
  if (year === 6) {
    return 'M2';
  }
  if (year === 7) {
    return 'D1';
  }
  if (year === 8) {
    return 'D2';
  }
  if (year === 9) {
    return 'D3';
  }
  if (year === 10) {
    return 'その他';
  }
  return '未設定';
}

/**
 * Helper function to get faculty abbreviation
 */
export function getFacultyAbbreviation(faculty: string | null): string {
  if (!faculty) {
    return '未設定';
  }
  
  const abbreviations: Record<string, string> = {
    '文学部': '文',
    '教育学部': '教',
    '法学部': '法', 
    '経済学部': '経',
    '理学部': '理',
    '医学部': '医',
    '歯学部': '歯',
    '薬学部': '薬',
    '工学部': '工',
    '芸術工学部': '芸工',
    '農学部': '農',
    '共創学部': '共創',
  };
  
  return abbreviations[faculty] || faculty;
}