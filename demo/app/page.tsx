import Hero from '@/components/Hero'
import PipelineFlow from '@/components/PipelineFlow'
import DemoSection from '@/components/DemoSection'
import MetricsSection from '@/components/MetricsSection'

export default function Home() {
  return (
    <main className="min-h-screen">
      <Hero />
      <PipelineFlow />
      <DemoSection />
      <MetricsSection />
      <footer className="border-t border-white/5 py-10 text-center text-sm text-gray-600">
        <p>
          Built on GCP · Vertex AI · BigQuery · GKE · Prometheus ·{' '}
          <a
            href="https://github.com/shoraaz/promo-roi-platform"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-500 hover:text-gray-300 transition-colors underline underline-offset-2"
          >
            Source on GitHub
          </a>
        </p>
      </footer>
    </main>
  )
}
