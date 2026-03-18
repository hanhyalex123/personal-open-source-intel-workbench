import { ConfigProvider } from "antd";

import antdTheme from "../theme/antdTheme";

export default function AppProviders({ children }) {
  return <ConfigProvider theme={antdTheme}>{children}</ConfigProvider>;
}
