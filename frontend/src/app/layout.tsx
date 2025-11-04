'use client'

import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ApolloProvider } from '@apollo/client'
import { apolloClient } from '@/lib/apollo'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body className={inter.className}>
        <ApolloProvider client={apolloClient}>
          {children}
        </ApolloProvider>
      </body>
    </html>
  )
}

