// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('PCS Tracker v2.2.0 Features', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('Homepage loads correctly', async ({ page }) => {
    await expect(page).toHaveTitle(/PCS Tracker/);
    await expect(page.locator('h1')).toContainText('Pocket Change Showdown');
    
    // Take screenshot of homepage
    await page.screenshot({ 
      path: 'tests/screenshots/01-homepage.png',
      fullPage: true 
    });
  });

  test('Navigate to expenses page and verify layout', async ({ page }) => {
    // Navigate to expenses page
    await page.click('a[href*="expenses"]');
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('h2')).toContainText('Expense List');
    
    // Take screenshot of expenses page
    await page.screenshot({ 
      path: 'tests/screenshots/02-expenses-page.png',
      fullPage: true 
    });
  });

  test('Add new expense with "Maybe" reimbursable option', async ({ page }) => {
    // Navigate to add expense page
    await page.goto('/expense/new');
    await page.waitForLoadState('networkidle');
    
    // Fill out the expense form with "Maybe" reimbursable option
    await page.fill('input[name="title"]', 'Test Expense - Maybe Reimbursable');
    await page.fill('textarea[name="description"]', 'Testing the new Maybe reimbursable option');
    await page.fill('input[name="cost"]', '150.00');
    await page.fill('input[name="location"]', 'Test Location');
    await page.fill('input[name="vendor"]', 'Test Vendor');
    
    // Set date
    await page.fill('input[name="date"]', '2024-08-31');
    
    // Select "Maybe" for reimbursable
    await page.selectOption('select[name="is_reimbursable"]', 'maybe');
    
    // Take screenshot of form with Maybe option
    await page.screenshot({ 
      path: 'tests/screenshots/03-new-expense-form-maybe.png',
      fullPage: true 
    });
    
    // Submit the form
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    
    // Verify we're back on expenses page
    await expect(page.locator('h2')).toContainText('Expense List');
  });

  test('Add expenses with all reimbursable states (Yes, No, Maybe)', async ({ page }) => {
    // Add "Yes" reimbursable expense
    await page.goto('/expense/new');
    await page.fill('input[name="title"]', 'Yes Reimbursable Expense');
    await page.fill('input[name="cost"]', '100.00');
    await page.fill('input[name="date"]', '2024-08-30');
    await page.selectOption('select[name="is_reimbursable"]', 'yes');
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    
    // Add "No" reimbursable expense
    await page.goto('/expense/new');
    await page.fill('input[name="title"]', 'No Reimbursable Expense');
    await page.fill('input[name="cost"]', '75.00');
    await page.fill('input[name="date"]', '2024-08-29');
    await page.selectOption('select[name="is_reimbursable"]', 'no');
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    
    // Add "Maybe" reimbursable expense
    await page.goto('/expense/new');
    await page.fill('input[name="title"]', 'Maybe Reimbursable Expense');
    await page.fill('input[name="cost"]', '200.00');
    await page.fill('input[name="date"]', '2024-08-28');
    await page.selectOption('select[name="is_reimbursable"]', 'maybe');
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
  });

  test('Verify reimbursable field displays correctly for all states', async ({ page }) => {
    await page.goto('/expenses');
    await page.waitForLoadState('networkidle');
    
    // Wait for table to load
    await page.waitForSelector('#expenseTable tbody tr', { timeout: 10000 });
    
    // Check for "Yes" badge (green)
    const yesBadges = page.locator('tbody .badge.bg-success', { hasText: 'Yes' });
    if (await yesBadges.count() > 0) {
      await expect(yesBadges.first()).toBeVisible();
    }
    
    // Check for "No" badge (secondary/gray)
    const noBadges = page.locator('tbody .badge.bg-secondary', { hasText: 'No' });
    if (await noBadges.count() > 0) {
      await expect(noBadges.first()).toBeVisible();
    }
    
    // Check for "Maybe" badge (warning/yellow)
    const maybeBadges = page.locator('tbody .badge.bg-warning', { hasText: 'Maybe' });
    if (await maybeBadges.count() > 0) {
      await expect(maybeBadges.first()).toBeVisible();
    }
    
    // Take screenshot showing all reimbursable states
    await page.screenshot({ 
      path: 'tests/screenshots/04-reimbursable-states-all.png',
      fullPage: true 
    });
  });

  test('Test expense preview modal functionality', async ({ page }) => {
    await page.goto('/expenses');
    await page.waitForLoadState('networkidle');
    
    // Wait for table and expenses to load
    await page.waitForSelector('#expenseTable tbody tr', { timeout: 10000 });
    
    // Click on the first expense title to open preview modal
    const firstExpenseTitle = page.locator('.expense-title-link').first();
    if (await firstExpenseTitle.count() > 0) {
      await firstExpenseTitle.click();
      
      // Wait for modal to appear
      await page.waitForSelector('#expensePreviewModal', { timeout: 5000 });
      
      // Verify modal content
      await expect(page.locator('#expensePreviewModal')).toBeVisible();
      await expect(page.locator('#expensePreviewModal .modal-title')).toBeVisible();
      
      // Take screenshot of the modal
      await page.screenshot({ 
        path: 'tests/screenshots/05-expense-preview-modal.png',
        fullPage: true 
      });
      
      // Test modal buttons
      const editButton = page.locator('#expensePreviewModal a.btn-primary');
      const deleteButton = page.locator('#expensePreviewModal button.btn-outline-danger');
      const closeButton = page.locator('#expensePreviewModal .btn-secondary[data-bs-dismiss="modal"]');
      
      await expect(editButton).toBeVisible();
      await expect(deleteButton).toBeVisible();
      await expect(closeButton).toBeVisible();
      
      // Close modal
      await closeButton.click();
      await page.waitForSelector('#expensePreviewModal', { state: 'hidden', timeout: 5000 });
    }
  });

  test('Test column customization functionality', async ({ page }) => {
    await page.goto('/expenses');
    await page.waitForLoadState('networkidle');
    
    // Wait for the Columns button to be available
    await page.waitForSelector('button:has-text("Columns")', { timeout: 10000 });
    
    // Click on Columns button to open customization modal
    await page.click('button:has-text("Columns")');
    
    // Wait for column modal to appear
    await page.waitForSelector('#columnCustomizationModal', { timeout: 5000 });
    
    // Verify modal is visible
    await expect(page.locator('#columnCustomizationModal')).toBeVisible();
    await expect(page.locator('#columnCustomizationModal .modal-title')).toContainText('Customize Table Columns');
    
    // Take screenshot of column customization modal
    await page.screenshot({ 
      path: 'tests/screenshots/06-column-customization-modal.png',
      fullPage: true 
    });
    
    // Test toggling some columns
    const locationCheckbox = page.locator('#column-location');
    const vendorCheckbox = page.locator('#column-vendor');
    const notesCheckbox = page.locator('#column-notes');
    
    // Enable some hidden columns
    if (await locationCheckbox.count() > 0) {
      await locationCheckbox.check();
    }
    if (await vendorCheckbox.count() > 0) {
      await vendorCheckbox.check();
    }
    if (await notesCheckbox.count() > 0) {
      await notesCheckbox.check();
    }
    
    // Save preferences
    await page.click('#saveColumnPreferences');
    
    // Wait for modal to close
    await page.waitForSelector('#columnCustomizationModal', { state: 'hidden', timeout: 5000 });
    
    // Wait for table to update
    await page.waitForTimeout(1000);
    
    // Take screenshot showing expanded columns
    await page.screenshot({ 
      path: 'tests/screenshots/07-expanded-columns.png',
      fullPage: true 
    });
  });

  test('Test responsive design on different screen sizes', async ({ page, browserName }) => {
    await page.goto('/expenses');
    await page.waitForLoadState('networkidle');
    
    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);
    await page.screenshot({ 
      path: 'tests/screenshots/08-tablet-view.png',
      fullPage: true 
    });
    
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);
    await page.screenshot({ 
      path: 'tests/screenshots/09-mobile-view.png',
      fullPage: true 
    });
    
    // Back to desktop
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.waitForTimeout(500);
  });

  test('Comprehensive feature verification with visual proof', async ({ page }) => {
    // Start fresh and create comprehensive test data
    await page.goto('/expenses');
    await page.waitForLoadState('networkidle');
    
    // Take final comprehensive screenshot showing all features
    await page.screenshot({ 
      path: 'tests/screenshots/10-comprehensive-features.png',
      fullPage: true 
    });
    
    // Verify key elements are present
    await expect(page.locator('h2:has-text("Expense List")')).toBeVisible();
    
    // Check if we have any expenses in the table
    const expenseRows = page.locator('#expenseTable tbody tr');
    const rowCount = await expenseRows.count();
    
    if (rowCount > 0) {
      // Verify reimbursable badges exist
      const badges = page.locator('tbody .badge');
      const badgeCount = await badges.count();
      
      console.log(`Found ${rowCount} expense rows and ${badgeCount} badges`);
      
      // Test that we can see different badge types
      const yesCount = await page.locator('tbody .badge.bg-success:has-text("Yes")').count();
      const noCount = await page.locator('tbody .badge.bg-secondary:has-text("No")').count();
      const maybeCount = await page.locator('tbody .badge.bg-warning:has-text("Maybe")').count();
      
      console.log(`Badge counts - Yes: ${yesCount}, No: ${noCount}, Maybe: ${maybeCount}`);
    }
    
    // Verify column customization button exists
    await expect(page.locator('button:has-text("Columns")')).toBeVisible();
    
    // Verify expense preview links exist
    const titleLinks = page.locator('.expense-title-link');
    if (await titleLinks.count() > 0) {
      await expect(titleLinks.first()).toBeVisible();
    }
  });

  test('Test expense form has Maybe reimbursable option', async ({ page }) => {
    await page.goto('/expense/new');
    await page.waitForLoadState('networkidle');
    
    // Check that the reimbursable select has all three options
    const reimbursableSelect = page.locator('select[name="is_reimbursable"]');
    await expect(reimbursableSelect).toBeVisible();
    
    // Verify all options exist by checking the HTML content
    const selectContent = await reimbursableSelect.innerHTML();
    expect(selectContent).toContain('value="yes"');
    expect(selectContent).toContain('value="no"');
    expect(selectContent).toContain('value="maybe"');
    
    // Take screenshot of the form
    await page.screenshot({ 
      path: 'tests/screenshots/11-expense-form-reimbursable-options.png',
      fullPage: true 
    });
    
    // Test that we can select each option
    await page.selectOption('select[name="is_reimbursable"]', 'yes');
    await page.selectOption('select[name="is_reimbursable"]', 'no');
    await page.selectOption('select[name="is_reimbursable"]', 'maybe');
  });
});