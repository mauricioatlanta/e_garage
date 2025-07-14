
import { FaUsers, FaCar, FaFileInvoice, FaCogs, FaTools, FaChartLine } from "react-icons/fa";

const DashboardCard = ({ icon: Icon, title, href, color }) => (
  <a
    href={href}
    className="bg-white shadow-md hover:shadow-xl transition rounded-xl p-6 text-center hover:scale-105 duration-300"
  >
    <Icon className={\`text-3xl mb-3 \${color}\`} />
    <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
  </a>
);

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-100 px-4 py-12">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">¡Hola, bienvenido a TallerPro!</h1>
        <p className="text-gray-600 text-lg mb-8">
          Tu centro de control para gestionar clientes, vehículos y mucho más.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          <DashboardCard icon={FaUsers} title="Clientes" href="/clientes" color="text-blue-500" />
          <DashboardCard icon={FaCar} title="Vehículos" href="/vehiculos" color="text-green-500" />
          <DashboardCard icon={FaFileInvoice} title="Documentos" href="/documentos" color="text-yellow-500" />
          <DashboardCard icon={FaCogs} title="Repuestos" href="/repuestos" color="text-red-500" />
          <DashboardCard icon={FaTools} title="Servicios" href="/servicios" color="text-purple-500" />
          <DashboardCard icon={FaChartLine} title="Reportes" href="/reportes" color="text-indigo-500" />
        </div>
      </div>
    </div>
  );
}
