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

    // Wait for page to load - Header should be active agent name (Default: Dr. Elena Vasquez)
    await expect(page.getByRole('heading', { name: /Dr\. Elena Vasquez/i })).toBeVisible()

    // Verify instructions in the button
    await expect(page.getByRole('button', { name: /hold to speak/i })).toBeVisible()

    // Verify connection status indicator exists
    await expect(page.locator('.connection-status')).toBeVisible()
  })

  test('should display active agent details', async ({ page }) => {
    await page.goto('/voice')

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /Dr\. Elena Vasquez/i })).toBeVisible()

    // Verify role is displayed
    await expect(page.getByText('Business Analyst')).toBeVisible()
  })

  test('should have voice chat component initialized', async ({ page }) => {
    await page.goto('/voice')

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /Dr\. Elena Vasquez/i })).toBeVisible()

    // Verify the container is present (updated class name)
    const container = page.locator('.voice-page')
    await expect(container).toBeVisible()

    // Verify voice controls are present
    const controls = page.locator('.controls-section')
    await expect(controls).toBeVisible()
  })

  test('should be accessible from Chat & Voice navigation menu', async ({ page }) => {
    await page.goto('/')

    // Find and click the Chat & Voice menu item to expand it
    const chatVoiceSection = page.getByText('Chat & Voice')

    // Click voice interaction link
    await page.getByRole('button', { name: /voice interaction/i }).click()

    // Verify navigation
    await expect(page).toHaveURL('/voice')
    await expect(page.getByRole('heading', { name: /Dr\. Elena Vasquez/i })).toBeVisible()
  })
})
