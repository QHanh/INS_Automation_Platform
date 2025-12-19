import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import ToolCategory from './pages/ToolCategory';
import ToolPlaceholder from './components/ToolPlaceholder';
import PSSEBuildModel from './pages/psse/BuildModel';
import CheckReactive from './pages/psse/CheckReactive';
import PSSETuningTool from './pages/psse/TuningTool';
import PSCADBuildModel from './pages/pscad/BuildModel';
import PSCADCreateCases from './pages/pscad/CreateCases';
import PSCADConvertSimulink from './pages/pscad/ConvertSimulink';
import ETAPBuildModel from './pages/etap/BuildModel';
import './index.css';

function App() {
  const [isBackendReady, setIsBackendReady] = useState(false);

  useEffect(() => {
    const checkBackendHealth = async () => {
      const maxRetries = 30;
      let retries = 0;

      while (retries < maxRetries) {
        try {
          const response = await fetch('http://localhost:8123/');
          if (response.ok) {
            console.log('Backend is ready!');
            setIsBackendReady(true);
            return;
          }
        } catch (e) {
          console.log('Waiting for backend...');
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
        retries++;
      }
      alert('Backend failed to start after 30 seconds. Please check logs.');
    };

    checkBackendHealth();
  }, []);

  if (!isBackendReady) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-xl font-semibold text-gray-700">Starting backend...</p>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path=":category" element={<ToolCategory />} />

          {/* PSCAD specific routes */}
          <Route path="pscad/build-model" element={<PSCADBuildModel />} />
          <Route path="pscad/setup-case" element={<PSCADCreateCases />} />
          <Route path="pscad/convert-simulink" element={<PSCADConvertSimulink />} />

          {/* PSS/E specific routes */}
          <Route path="psse/build-model" element={<PSSEBuildModel />} />
          <Route path="psse/check-reactive" element={<CheckReactive />} />
          <Route path="psse/tuning-tool" element={<PSSETuningTool />} />

          {/* ETAP specific routes */}
          <Route path="etap/build-model" element={<ETAPBuildModel />} />

          {/* Generic tool route */}
          <Route path=":category/:toolId" element={<ToolPlaceholder />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
