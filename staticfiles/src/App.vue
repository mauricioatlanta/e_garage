
<template>
  <div class="min-h-screen bg-[#0d1117] text-white p-6">
    <h1 class="text-3xl font-bold text-center mb-6">Servicios por Categoría</h1>

    <div v-if="loading" class="text-center text-gray-400">Cargando...</div>

    <div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 mb-8">
      <button
        v-for="cat in categorias"
        :key="cat.id"
        @click="seleccionarCategoria(cat)"
        class="h-20 text-lg font-semibold bg-[#161b22] hover:bg-[#21262d] border border-[#30363d] rounded-xl"
      >
        {{ cat.nombre }}
      </button>
    </div>

    <div v-if="categoriaSeleccionada" class="bg-[#161b22] p-4 rounded-xl">
      <h2 class="text-2xl font-bold mb-4">Subcategorías de {{ categoriaSeleccionada.nombre }}</h2>

      <ul>
        <li v-for="sub in categoriaSeleccionada.subcategorias" :key="sub.id" class="py-1 pl-2 border-l border-gray-600">
          🔧 {{ sub.nombre }}
        </li>
      </ul>

      <div class="mt-4 flex">
        <input v-model="nuevaSubcategoria" class="bg-[#0d1117] border border-[#30363d] px-3 py-1 rounded text-white w-full mr-2" placeholder="Nueva subcategoría" />
        <button @click="agregarSubcategoria" class="bg-green-600 hover:bg-green-500 px-4 py-1 rounded">Agregar</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const categorias = ref([])
const categoriaSeleccionada = ref(null)
const nuevaSubcategoria = ref('')
const loading = ref(true)

async function cargarCategorias() {
  try {
    const res = await fetch('http://localhost:8000/api/categorias/')
    const data = await res.json()
    categorias.value = data
  } catch (err) {
    console.error('Error cargando categorías:', err)
  } finally {
    loading.value = false
  }
}

async function agregarSubcategoria() {
  if (!nuevaSubcategoria.value.trim() || !categoriaSeleccionada.value) return

  const nueva = {
    nombre: nuevaSubcategoria.value,
    categoria: categoriaSeleccionada.value.id
  }

  const res = await fetch('http://localhost:8000/api/subcategorias/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(nueva)
  })

  const subcreada = await res.json()
  categoriaSeleccionada.value.subcategorias.push(subcreada)
  nuevaSubcategoria.value = ''
}

function seleccionarCategoria(cat) {
  categoriaSeleccionada.value = cat
  nuevaSubcategoria.value = ''
}
onMounted(cargarCategorias)
</script>
