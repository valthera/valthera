import { Link } from 'react-router-dom'
import { Zap, LogIn, ArrowRight, Brain, Cpu, Layers } from 'lucide-react'
import { Button } from '../components/ui/button'

export function Landing() {
  return (
    <div className="flex flex-col min-h-screen bg-white text-black">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 bg-white/95 backdrop-blur-sm z-50 border-b border-black/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <img src="/logo.svg" alt="Valthera" className="h-14 w-14" />
            </div>
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="lg" className="text-black/80 hover:text-black hover:bg-black/5" asChild>
                <Link to="/signin">
                  <LogIn className="mr-2 h-4 w-4" />
                  Sign In
                </Link>
              </Button>
              <Button size="lg" className="bg-black text-white hover:bg-black/90" asChild>
                <Link to="/signup">
                  Get Started
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-grow">
        <section className="pt-32 pb-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
              <span className="block text-gray-600">Stream robot clips for insights,</span>
              <span className="block text-black">hosted and ready to deploy.</span>
            </h1>
            <p className="mt-6 max-w-3xl mx-auto text-xl text-gray-600 leading-relaxed">
              The fastest way to understand, classify, and predict behavior using
              foundation models like V-JEPA 2 — no infrastructure or research team
              required.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="text-lg px-8 py-6" asChild>
                <Link to="/signup">
                  Get Started
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button variant="outline" size="lg" className="text-lg px-8 py-6" asChild>
                <Link to="/signin">
                  Sign In
                </Link>
              </Button>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-black mb-4">
                Built for Modern AI Applications
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Deploy state-of-the-art perception models without the complexity
              </p>
            </div>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center p-8 bg-white rounded-lg border border-gray-200">
                <div className="inline-flex items-center justify-center w-12 h-12 bg-black text-white rounded-lg mb-6">
                  <Brain className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-semibold text-black mb-4">Foundation Models</h3>
                <p className="text-gray-600">
                  Access cutting-edge models like V-JEPA 2 for advanced video understanding and behavior prediction
                </p>
              </div>
              <div className="text-center p-8 bg-white rounded-lg border border-gray-200">
                <div className="inline-flex items-center justify-center w-12 h-12 bg-black text-white rounded-lg mb-6">
                  <Cpu className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-semibold text-black mb-4">Hosted Infrastructure</h3>
                <p className="text-gray-600">
                  No need to manage servers or GPU clusters. We handle all the infrastructure for you
                </p>
              </div>
              <div className="text-center p-8 bg-white rounded-lg border border-gray-200">
                <div className="inline-flex items-center justify-center w-12 h-12 bg-black text-white rounded-lg mb-6">
                  <Layers className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-semibold text-black mb-4">Easy Integration</h3>
                <p className="text-gray-600">
                  Simple APIs and SDKs to integrate AI perception into your applications quickly
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 bg-black text-white">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">
              Ready to get started?
            </h2>
            <p className="text-xl text-gray-300 mb-8">
              Join developers building the next generation of AI-powered systems
            </p>
            <Button size="lg" variant="secondary" className="text-lg px-8 py-6" asChild>
              <Link to="/signup">
                Start Building
                <Zap className="ml-2 h-5 w-5" />
              </Link>
            </Button>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-black/10">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center items-center">
            <p className="text-xs font-mono text-black/40">
              © 2025 Valthera LLC
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
} 