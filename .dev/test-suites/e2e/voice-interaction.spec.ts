import { test, expect } from '@playwright/test'

test.describe('Voice Interaction', () => {
  test('should navigate to voice interaction page', async ({ page }) => {
    await page.goto('/')

    // Wait for TreeNav to be visible
    await expect(page.getByText('Chat & Voice')).toBeVisible()

    // Click on Voice Interaction
    const voiceButton = page.getByRole('button', { name: /voice interaction/i })
    await voiceButton.click()

    // Should navigate to voice page
    await expect(page).toHaveURL('/voice')
  })

  test('should display voice interaction page content', async ({ page }) => {
    await page.goto('/voice')

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /voice interaction/i })).toBeVisible()

    // Verify instructions
    await expect(page.getByText(/press and hold to speak/i)).toBeVisible()

    // Verify connection status section
    await expect(page.getByText(/connection status/i)).toBeVisible()
  })

  test('should display different agent names', async ({ page }) => {
    await page.goto('/voice')

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /voice interaction/i })).toBeVisible()

    // Default should be Elena
    await expect(page.getByText(/interact with elena/i)).toBeVisible()
  })

  test('should have voice chat component initialized', async ({ page }) => {
    await page.goto('/voice')

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /voice interaction/i })).toBeVisible()

    // Verify the container is present
    const container = page.locator('.voice-interaction-container')
    await expect(container).toBeVisible()
  })

  test('should be accessible from Chat & Voice navigation menu', async ({ page }) => {
    await page.goto('/')

    // Find and click the Chat & Voice menu item to expand it
    const chatVoiceSection = page.getByText('Chat & Voice')
    
    // Click voice interaction link
    await page.getByRole('button', { name: /voice interaction/i }).click()

    // Verify navigation
    await expect(page).toHaveURL('/voice')
    await expect(page.getByRole('heading', { name: /voice interaction/i })).toBeVisible()
  })
})
