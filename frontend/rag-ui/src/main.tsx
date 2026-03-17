import '@gravity-ui/uikit/styles/fonts.css';
import '@gravity-ui/uikit/styles/styles.css';
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ThemeProvider } from '@gravity-ui/uikit';
import {Provider} from 'react-redux';
import {store} from './app/store';
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Provider store={store}>
      <ThemeProvider theme="dark">
        <App />
      </ThemeProvider>
    </Provider>
  </StrictMode>,
)
