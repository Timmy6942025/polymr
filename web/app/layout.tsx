import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Polymr - Market Making Bot",
  description: "Automated market making on Polymarket prediction markets",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  )
}
