import {defineConfig} from "@playwright/test";
export default defineConfig({
  testDir:"./tests",workers:1,timeout:45000,
  use:{baseURL:"http://127.0.0.1:3000",trace:"retain-on-failure",screenshot:"only-on-failure"},
  webServer:[
    {command:process.platform==="win32"?'"..\\.venv\\Scripts\\python.exe" ../scripts/pilot_test_server.py':"../.venv/bin/python ../scripts/pilot_test_server.py",url:"http://127.0.0.1:8000/health",reuseExistingServer:!process.env.CI,timeout:30000},
    {command:"npm run start -- --hostname 127.0.0.1",url:"http://127.0.0.1:3000",reuseExistingServer:!process.env.CI,timeout:30000},
  ],
});
