import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { get, post, patch, del, put, ApiError, NetworkError } from '../../lib/api'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('GET requests', () => {
    it('should make successful GET request', async () => {
      const mockResponse = { data: 'test' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
      })

      const result = await get('/test')
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          method: 'GET',
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle GET request with query parameters', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
      })

      await get('/test', { params: { page: 1, limit: 20 } })
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('page=1'),
        expect.anything()
      )
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('limit=20'),
        expect.anything()
      )
    })

    it('should handle 204 No Content response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      })

      const result = await get('/test')
      expect(result).toBeNull()
    })
  })

  describe('POST requests', () => {
    it('should make successful POST request with body', async () => {
      const requestBody = { title: 'Test', body: 'Content' }
      const mockResponse = { id: '123', ...requestBody }
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      })

      const result = await post('/test', requestBody)
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(requestBody),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should set Content-Type header for JSON body', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({}),
      })

      await post('/test', { data: 'test' })
      
      const call = mockFetch.mock.calls[0]
      const headers = call[1].headers
      expect(headers.get('Content-Type')).toBe('application/json')
    })
  })

  describe('PATCH requests', () => {
    it('should make successful PATCH request', async () => {
      const requestBody = { title: 'Updated' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => requestBody,
      })

      const result = await patch('/test/123', requestBody)
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/test/123'),
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(requestBody),
        })
      )
      expect(result).toEqual(requestBody)
    })
  })

  describe('DELETE requests', () => {
    it('should make successful DELETE request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      })

      const result = await del('/test/123')
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/test/123'),
        expect.objectContaining({
          method: 'DELETE',
        })
      )
      expect(result).toBeNull()
    })
  })

  describe('PUT requests', () => {
    it('should make successful PUT request with JSON', async () => {
      const requestBody = { data: 'test' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => requestBody,
      })

      const result = await put('/test', requestBody)
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(requestBody),
        })
      )
      expect(result).toEqual(requestBody)
    })

    it('should handle FormData for file uploads', async () => {
      const formData = new FormData()
      formData.append('file', new Blob(['test']))
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      })

      await put('/upload', formData)
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/upload'),
        expect.objectContaining({
          method: 'PUT',
          body: formData,
        })
      )
    })
  })

  describe('Error handling', () => {
    it('should throw ApiError for HTTP errors', async () => {
      const errorResponse = {
        error: {
          code: 'NOT_FOUND',
          message: 'Resource not found',
          requestId: 'req_123',
        },
      }
      
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => errorResponse,
      })

      try {
        await get('/test')
        expect.fail('Should have thrown an error')
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError)
        expect(error).toMatchObject({
          status: 404,
          code: 'NOT_FOUND',
          message: 'Resource not found',
          requestId: 'req_123',
        })
      }
    })

    it('should handle non-JSON error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      await expect(get('/test')).rejects.toMatchObject({
        status: 500,
        code: 'UNKNOWN_ERROR',
        message: 'HTTP 500: Internal Server Error',
      })
    })

    it('should throw NetworkError for network failures', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network failed'))

      await expect(get('/test')).rejects.toThrow(NetworkError)
      await expect(get('/test')).rejects.toMatchObject({
        message: 'Network request failed',
      })
    })

    it('should handle request timeout', async () => {
      // Create an AbortController that we can manually abort
      const abortError = new Error('The operation was aborted')
      abortError.name = 'AbortError'
      
      mockFetch.mockRejectedValueOnce(abortError)

      try {
        await get('/test', { timeout: 100 })
        expect.fail('Should have thrown a timeout error')
      } catch (error) {
        expect(error).toBeInstanceOf(NetworkError)
        expect(error.message).toBe('Request timeout')
      }
    })
  })

  describe('Authorization', () => {
    it('should add Bearer token when provided', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({}),
      })

      await get('/test', { token: 'test-token-123' })
      
      const call = mockFetch.mock.calls[0]
      const headers = call[1].headers
      expect(headers.get('Authorization')).toBe('Bearer test-token-123')
    })
  })
})