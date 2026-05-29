import React, { useState, useEffect } from 'react';
import { FaList, FaCheckCircle, FaArrowRight } from 'react-icons/fa';

const StepsGuide = ({ modulo = null }) => {
  const [pasos, setPasos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedGuide, setSelectedGuide] = useState(null);

  useEffect(() => {
    const fetchPasos = async () => {
      try {
        const url = modulo ? `/help/api/pasos/${modulo}/` : '/help/api/pasos/';
        const response = await fetch(url);
        const data = await response.json();
        setPasos(data.pasos || []);
      } catch (error) {
        console.error('Error fetching pasos:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPasos();
  }, [modulo]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <FaList className="text-6xl text-blue-600 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Guías Paso a Paso
            {modulo && <span className="text-blue-600"> - {modulo.charAt(0).toUpperCase() + modulo.slice(1)}</span>}
          </h1>
          <p className="text-gray-600 text-lg">
            Sigue estas guías para completar tareas comunes de manera eficiente
          </p>
        </div>

        {/* Guides List */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-8">
          {pasos.length > 0 ? (
            pasos.map((guia, index) => (
              <div
                key={index}
                onClick={() => setSelectedGuide(selectedGuide === index ? null : index)}
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-all cursor-pointer overflow-hidden"
              >
                <div className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-800">{guia.titulo}</h3>
                    <FaArrowRight className={`text-gray-400 transition-transform ${
                      selectedGuide === index ? 'rotate-90' : ''
                    }`} />
                  </div>
                  <p className="text-gray-600 text-sm mb-4">
                    {guia.pasos.length} paso{guia.pasos.length !== 1 ? 's' : ''} recomendado{guia.pasos.length !== 1 ? 's' : ''}
                  </p>
                  {selectedGuide === index && (
                    <div className="border-t pt-4">
                      <ol className="space-y-3">
                        {guia.pasos.map((paso, pasoIndex) => (
                          <li key={pasoIndex} className="flex items-start">
                            <FaCheckCircle className="text-green-500 mt-0.5 mr-3 flex-shrink-0" />
                            <span className="text-gray-700 text-sm">{paso}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full text-center py-12">
              <FaList className="text-6xl text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">
                No hay guías disponibles
              </h3>
              <p className="text-gray-500">
                {modulo
                  ? `No se encontraron guías paso a paso para el módulo ${modulo}.`
                  : 'No hay guías paso a paso disponibles actualmente.'
                }
              </p>
            </div>
          )}
        </div>

        {/* Selected Guide Detail */}
        {selectedGuide !== null && (
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              {pasos[selectedGuide].titulo}
            </h2>
            <div className="space-y-4">
              {pasos[selectedGuide].pasos.map((paso, index) => (
                <div key={index} className="flex items-start">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-semibold mr-4">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <p className="text-gray-800 leading-relaxed">{paso}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center">
          <p className="text-gray-600 mb-4">
            ¿Necesitas más ayuda o tienes preguntas específicas?
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/help/"
              className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Centro de Ayuda Completo
            </a>
            <a
              href="/help/buscar/"
              className="inline-block bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors font-medium"
            >
              Buscar Artículos
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StepsGuide;