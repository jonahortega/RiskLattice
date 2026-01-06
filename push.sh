#!/bin/bash

cd /Users/jonahortega/risklattice

echo "Initializing git..."
git init

echo "Adding remote..."
git remote remove origin 2>/dev/null
git remote add origin https://github.com/jonahortega/RiskLattice.git

echo "Adding files..."
git add .

echo "Committing..."
git commit -m "Initial commit: RiskLattice - AI Financial Risk Intelligence Platform"

echo "Setting main branch..."
git branch -M main

echo "Pushing to GitHub..."
git push -u origin main

echo "Done! Check https://github.com/jonahortega/RiskLattice to verify."

