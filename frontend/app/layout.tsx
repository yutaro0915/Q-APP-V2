import type { Metadata } from 'next'
import { Noto_Sans_JP } from 'next/font/google'
import './globals.css'

const notoSansJP = Noto_Sans_JP({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  display: 'swap',
  variable: '--font-noto-sans-jp',
  fallback: ['Hiragino Kaku Gothic ProN', 'Hiragino Sans', 'Meiryo', 'sans-serif'],
})

export const metadata: Metadata = {
  title: '九大学内SNS',
  description: '九州大学の学生・教職員向けSNS',
  keywords: ['九州大学', 'SNS', 'Q&A', 'ディスカッション'],
  authors: [{ name: 'Kyudai Campus SNS Team' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0a0a0a' },
  ],
  formatDetection: {
    telephone: false,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja" className={notoSansJP.variable}>
      <body className={`${notoSansJP.className} antialiased`}>
        {/* Future header placement */}
        <div className="min-h-screen flex flex-col">
          <main className="flex-1">
            {children}
          </main>
          {/* Future footer placement */}
        </div>
      </body>
    </html>
  )
}