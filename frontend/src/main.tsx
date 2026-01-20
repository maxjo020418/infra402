import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './styles.css'
import { Providers } from './Providers.tsx'
import '@coinbase/onchainkit/styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Providers>
      <App />
    </Providers>
  </React.StrictMode>,
)
