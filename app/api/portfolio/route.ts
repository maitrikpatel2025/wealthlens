import { NextResponse } from 'next/server'
import { mockPortfolio } from '@/lib/mockData'

export async function GET() {
  return NextResponse.json(mockPortfolio)
}
