import {test,expect} from "@playwright/test";

test("public pages and responsive navigation",async({page})=>{
  await page.goto("/");await expect(page.getByRole("heading",{level:1})).toContainText("Your next contract");
  await page.screenshot({path:"test-results/landing-desktop.png",fullPage:true});
  for(const path of ["/features","/pricing","/how-it-works","/faq","/privacy","/terms","/cookies","/example-report","/contact"]){await page.goto(path);await expect(page.getByRole("heading",{level:1})).toBeVisible();}
  await page.setViewportSize({width:390,height:844});await page.goto("/");await expect(page.getByRole("link",{name:"Find your opportunities"})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();await page.screenshot({path:"test-results/landing-mobile.png",fullPage:true});
});

test("complete verified customer workflow with real local API",async({page,request})=>{
  const email=`pilot${Date.now()}@example.com`;
  await page.goto("/auth/signup");await page.getByLabel("Email address").fill(email);await page.getByLabel("Company name").fill("Browser pilot SME");await page.getByLabel("Password",{exact:true}).fill("Browser test password 927!");await page.getByRole("checkbox").check();await page.getByRole("button",{name:"Create your account"}).click();await expect(page.getByRole("status")).toContainText("verification email");
  const token=await(await request.get(`http://127.0.0.1:8000/__test/token?email=${encodeURIComponent(email)}`)).json();
  await page.goto(`/auth/verify#token=${token.token}`);await page.getByRole("button",{name:"Verify email",exact:true}).click();await expect(page.getByRole("status")).toContainText("Email verified");
  await page.goto("/auth/login");await page.getByLabel("Email address").fill(email);await page.getByLabel("Password",{exact:true}).fill("Browser test password 927!");await page.getByRole("button",{name:"Sign in",exact:true}).click();await expect(page).toHaveURL(/dashboard/);
  await page.getByRole("link",{name:"Set up your company"}).click();await page.getByLabel("Company name",{exact:true}).fill("Security SME");await page.getByLabel("What does your company deliver?").fill("cybersecurity software development");await page.getByRole("button",{name:"Continue"}).click();await page.getByLabel("Services offered").fill("software, cybersecurity");await page.getByLabel("Skills & specializations").fill("Python");await page.getByRole("button",{name:"Continue"}).click();await page.getByRole("button",{name:"Save company profile"}).click();await expect(page.getByRole("heading",{name:"Your profile is ready."})).toBeVisible();
  await page.goto("/dashboard");await page.getByRole("button",{name:"Refresh matches"}).click();await expect(page.getByRole("heading",{name:/TEST FIXTURE: Cybersecurity/})).toBeVisible();await page.getByRole("button",{name:"Save",exact:true}).click();await expect(page.getByRole("status")).toContainText("Saved to your shortlist");
  await page.getByRole("link",{name:"Saved opportunities",exact:true}).click();await expect(page.getByRole("heading",{name:/TEST FIXTURE/})).toBeVisible();
  await page.goto("/notifications");await page.getByLabel("Digest frequency").selectOption("off");await page.getByRole("button",{name:"Save email preferences"}).click();await expect(page.getByRole("status")).toContainText("Changes saved");
  await page.goto("/billing");await expect(page.getByRole("main").getByText("professional · trialing",{exact:true})).toBeVisible();await page.getByRole("button",{name:"Test Starter checkout"}).click();await expect(page.getByRole("alert").filter({hasText:"test-mode key"})).toBeVisible();
  await page.setViewportSize({width:390,height:844});await page.goto("/dashboard");await expect(page.getByRole("heading",{level:1})).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.screenshot({path:"test-results/dashboard-mobile.png",fullPage:true});
  await page.getByRole("button",{name:"Sign out"}).click();await expect(page).toHaveURL(/auth\/login/);
});
