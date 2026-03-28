import React, { useState, useEffect } from 'react';
import { FaQuestionCircle, FaList, FaBook, FaChevronDown, FaChevronUp } from 'react-icons/fa';

const HelpPanel = ({ modulo = null }) => {
  const [config, setConfig] = useState(null);
  const [faqs, setFaqs] = useState([]);
  const [pasos, setPasos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('faqs');
  const [expandedFaq, setExpandedFaq] = useState(null);

  useEffect(() => {
    const fetchHelpData = async () => {
      try {
        // Fetch configuración del panel
        const configResponse = await fetch('/help/api/config/');
        const configData = await configResponse.json();
        setConfig(configData);

        // Fetch FAQs
        const faqUrl = modulo ? `/help/api/faqs/${modulo}/` : '/help/api/faqs/';
        const faqResponse = await fetch(faqUrl);
        const faqData = await faqResponse.json();
        setFaqs(faqData.faqs);

        // Fetch pasos recomendados
        const pasosUrl = modulo ? `/help/api/pasos/${modulo}/` : '/help/api/pasos/';
        const pasosResponse = await fetch(pasosUrl);
        const pasosData = await pasosResponse.json();
        setPasos(pasosData.pasos);

      } catch (error) {
        console.error('Error fetching help data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHelpData();
  }, [modulo]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Header */}
      <div className="bg-blue-600 text-white p-4">
        <div className="flex items-center">
          <FaQuestionCircle className="text-2xl mr-3" />
          <div>
            <h2 className="text-xl font-bold">Centro de Ayuda</h2>
            <p className="text-blue-100 text-sm">
              {modulo ? `Ayuda específica para ${modulo}` : 'Encuentra respuestas y guías'}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b">
        {config?.secciones.map((seccion) => (
          <button
            key={seccion.tipo}
            onClick={() => setActiveSection(seccion.tipo)}
            className={`flex-1 py-3 px-4 text-center font-medium transition-colors ${
              activeSection === seccion.tipo
                ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            {seccion.tipo === 'articulos' && <FaBook className="inline mr-2" />}
            {seccion.tipo === 'faqs' && <FaQuestionCircle className="inline mr-2" />}
            {seccion.tipo === 'pasos' && <FaList className="inline mr-2" />}
            {seccion.titulo}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-6 max-h-96 overflow-y-auto">
        {activeSection === 'faqs' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              Preguntas Frecuentes {modulo && ` - ${modulo.charAt(0).toUpperCase() + modulo.slice(1)}`}
            </h3>
            {Array.isArray(faqs) && faqs.length > 0 ? (
              faqs.map((faq, index) => (
                <div key={index} className="border rounded-lg">
                  <button
                    onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                    className="w-full text-left p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-gray-800">{faq.pregunta}</span>
                      {expandedFaq === index ? <FaChevronUp /> : <FaChevronDown />}
                    </div>
                  </button>
                  {expandedFaq === index && (
                    <div className="px-4 pb-4 text-gray-600">
                      {faq.respuesta}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-8">
                No hay preguntas frecuentes disponibles para este módulo.
              </p>
            )}
          </div>
        )}

        {activeSection === 'pasos' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              Pasos Recomendados {modulo && ` - ${modulo.charAt(0).toUpperCase() + modulo.slice(1)}`}
            </h3>
            {Array.isArray(pasos) && pasos.length > 0 ? (
              pasos.map((paso, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <h4 className="font-semibold text-gray-800 mb-3">{paso.titulo}</h4>
                  <ol className="list-decimal list-inside space-y-2 text-gray-600">
                    {paso.pasos.map((step, stepIndex) => (
                      <li key={stepIndex} className="text-sm">{step}</li>
                    ))}
                  </ol>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-8">
                No hay guías paso a paso disponibles para este módulo.
              </p>
            )}
          </div>
        )}

        {activeSection === 'articulos' && (
          <div className="text-center py-8">
            <FaBook className="text-4xl text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Artículos de Ayuda</h3>
            <p className="text-gray-600 mb-4">
              Encuentra guías detalladas y tutoriales completos.
            </p>
            <a
              href="/help/"
              className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Ver Todos los Artículos
            </a>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-gray-50 px-6 py-4 border-t">
        <div className="flex justify-between items-center text-sm text-gray-600">
          <span>¿No encuentras lo que buscas?</span>
          <a href="/help/" className="text-blue-600 hover:text-blue-800 font-medium">
            Centro de Ayuda Completo →
          </a>
        </div>
      </div>
    </div>
  );
};

export default HelpPanel;