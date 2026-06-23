import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Promo ROI Platform — Live Demo',
  description:
    'Production GCP ML system that predicts retail promotion profitability. Dual XGBoost models with SHAP explainability.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
