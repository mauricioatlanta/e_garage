import React, { useState, useEffect } from 'react';
import { FaSearch, FaChevronDown, FaChevronUp } from 'react-icons/fa';

const FAQScreen = ({ modulo = null }) => {
  const [faqs, setFaqs] = useState([]);
  const [filteredFaqs, setFilteredFaqs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedFaq, setExpandedFaq] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    const fetchFaqs = async () => {
      try {
        const url = modulo ? `/help/api/faqs/${modulo}/` : '/help/api/faqs/';
        const response = await fetch(url);
        const data = await response.json();

        // Si no es por módulo, aplanar las FAQs por categoría
        let faqList = [];
        if (modulo) {
          faqList = data.faqs || [];
        } else {
          // Aplanar FAQs de todas las categorías
          Object.entries(data.faqs || {}).forEach(([category, categoryFaqs]) => {
            categoryFaqs.forEach(faq => {
              faqList.push({ ...faq, category });
            });
          });
        }

        setFaqs(faqList);
        setFilteredFaqs(faqList);
      } catch (error) {
        console.error('Error fetching FAQs:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchFaqs();
  }, [modulo]);

  useEffect(() => {
    let filtered = faqs;

    // Filtrar por búsqueda
    if (searchTerm) {
      filtered = filtered.filter(faq =>
        faq.pregunta.toLowerCase().includes(searchTerm.toLowerCase()) ||
        faq.respuesta.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filtrar por categoría
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(faq => faq.category === selectedCategory);
    }

    setFilteredFaqs(filtered);
  }, [searchTerm, selectedCategory, faqs]);

  const categories = [...new Set(faqs.map(faq => faq.category))];

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
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Preguntas Frecuentes
            {modulo && <span className="text-blue-600"> - {modulo.charAt(0).toUpperCase() + modulo.slice(1)}</span>}
          </h1>
          <p className="text-gray-600 text-lg">
            Encuentra respuestas rápidas a las preguntas más comunes
          </p>
        </div>

        {/* Search and Filter */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <FaSearch className="absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar preguntas..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Category Filter */}
            {!modulo && categories.length > 1 && (
              <div className="md:w-48">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">Todas las categorías</option>
                  {categories.map(category => (
                    <option key={category} value={category}>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* FAQ List */}
        <div className="space-y-4">
          {filteredFaqs.length > 0 ? (
            filteredFaqs.map((faq, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md overflow-hidden">
                <button
                  onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                  className="w-full text-left p-6 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-800 mb-1">
                        {faq.pregunta}
                      </h3>
                      {!modulo && (
                        <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                          {faq.category}
                        </span>
                      )}
                    </div>
                    <div className="ml-4">
                      {expandedFaq === index ? (
                        <FaChevronUp className="text-gray-400" />
                      ) : (
                        <FaChevronDown className="text-gray-400" />
                      )}
                    </div>
                  </div>
                </button>

                {expandedFaq === index && (
                  <div className="px-6 pb-6 border-t border-gray-100">
                    <div className="pt-4 text-gray-700 leading-relaxed">
                      {faq.respuesta}
                    </div>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-12">
              <FaSearch className="text-6xl text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">
                No se encontraron resultados
              </h3>
              <p className="text-gray-500">
                Intenta con otros términos de búsqueda o verifica la categoría seleccionada.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-12">
          <p className="text-gray-600 mb-4">
            ¿No encuentras la respuesta que buscas?
          </p>
          <a
            href="/help/"
            className="inline-block bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Visitar Centro de Ayuda Completo
          </a>
        </div>
      </div>
    </div>
  );
};

export default FAQScreen;