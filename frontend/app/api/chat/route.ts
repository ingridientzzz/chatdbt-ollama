import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Validate request body
    if (!body.message || typeof body.message !== 'string') {
      return NextResponse.json(
        { error: 'Message is required and must be a string' },
        { status: 400 }
      )
    }

    // Forward request to backend
    const backendResponse = await fetch(`${BACKEND_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: body.message }),
    })

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({}))
      return NextResponse.json(
        { 
          error: errorData.detail || `Backend error: ${backendResponse.status}`,
          status: backendResponse.status
        },
        { status: backendResponse.status }
      )
    }

    const data = await backendResponse.json()
    
    return NextResponse.json({
      response: data.response,
      sources: data.sources || []
    })

  } catch (error) {
    console.error('API Route Error:', error)
    
    // Handle different types of errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return NextResponse.json(
        { 
          error: 'Cannot connect to backend server. Please ensure the backend is running.',
          details: 'Check that the backend server is started and accessible at ' + BACKEND_URL
        },
        { status: 503 }
      )
    }
    
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}

export async function GET() {
  return NextResponse.json({
    message: 'ChatDBT API is running',
    backend_url: BACKEND_URL,
    endpoints: {
      chat: 'POST /api/chat',
      health: 'GET /api/health'
    }
  })
}