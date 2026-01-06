#!/bin/bash

echo "🚀 Starting RiskLattice Frontend..."
echo ""

cd "$(dirname "$0")/frontend"

echo "📦 Installing packages (first time only, this takes 1-2 minutes)..."
npm install

echo ""
echo "✨ Starting server..."
echo "📍 Open your browser to the URL shown below!"
echo ""

npm run dev

