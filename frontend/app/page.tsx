export default function Home() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 text-gray-900 dark:text-gray-100">
            九大学内SNS
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            九州大学の学生・教職員向けQ&A・ディスカッションプラットフォーム
          </p>
        </header>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg p-8 shadow-sm border border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-semibold mb-4">
            まもなく公開
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            現在、システムの準備を進めています。
            もうしばらくお待ちください。
          </p>
          
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
              <span>質問・回答機能</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
              <span>ディスカッション機能</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
              <span>リアクション機能</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}