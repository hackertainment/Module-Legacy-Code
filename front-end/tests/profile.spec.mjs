import {test, expect} from "@playwright/test";
import {TIMELINE_USERNAMES_ELEMENTS_LOCATOR, loginAsSample, loginAsJustSomeGuy, waitForLocatorToHaveMatches} from "./test-utils.mjs";

test.describe("Profile View", () => {
  test("shows own profile when logged in", async ({page}) => {
    // Given a profile view
    // When I am logged in as sample
    await loginAsSample(page);
    await page.goto("/#/profile/sample");

    // Then I see logout button, profile, and timeline of my posts only
    await expect(
      page.locator("#logout-container [data-logout-button]")
    ).toBeVisible();
    await expect(
      page.locator("#profile-container header a[data-username]")
    ).toBeVisible();

    await waitForLocatorToHaveMatches(page, TIMELINE_USERNAMES_ELEMENTS_LOCATOR);
    const postUsernames = new Set(await page.locator(TIMELINE_USERNAMES_ELEMENTS_LOCATOR).allInnerTexts());
    expect(postUsernames).toEqual(new Set(["sample"]));

    // And bloom form is not attached
    await expect(
      page.locator("#bloom-form-container [data-form]")
    ).not.toBeAttached();
  });

  test("shows other user's profile with follow button", async ({page}) => {
    // Given I am logged in as AS
    await loginAsJustSomeGuy(page);
    // When I go to sample's profile
    await page.goto("/#/profile/sample");

    // Then I see logout button, profile, and timeline of sample's posts
    await expect(
      page.locator("#logout-container [data-logout-button]")
    ).toBeVisible();
    await expect(
      page.locator("#profile-container header a[data-username]")
    ).toBeVisible();
    await expect(page.locator("#timeline-container")).toBeVisible();
    // And bloom form is not attached
    await expect(page.locator("#bloom-form-container form")).not.toBeAttached();
  });

  test("allows unfollowing a user from their profile", async ({ page }) => {
    await signUp(page, "sample");
    await signUp(page, "AnotherUser");

    // Given a profile component AnotherUser
    // And I am logged in as sample
    await loginAsSample(page);
    await page.goto("/#/profile/AnotherUser");
    // And sample is following AS
    await page.click('[data-action="follow"]');

    // When I view the profile component for AnotherUser
    // Then I should see a button labeled "Unfollow"
    const unfollowButton = page.locator('[data-action="unfollow"]');
    await expect(unfollowButton).toBeVisible();

    // When I click the "Unfollow" button
    await unfollowButton.click();

    // Then I should no longer be following AnotherUser
    const followerCount = page.locator("[data-follower-count]");
    await expect(followerCount).toHaveText("0");
    // And the unfollow button is not visible
    await expect(unfollowButton).toBe("hidden");
  });
});
