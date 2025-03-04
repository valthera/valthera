import HeroImg from './assets/hero-img.webp';


const App = () => {
    
  return (
    <div className="flex flex-col min-h-screen bg-black text-white">
      {/* Header */}
      <header className="p-6 border-b border-gray-800">
        <div className="w-12 h-12 border border-white flex items-center justify-center">
          <span className="text-xl">(_)</span>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="flex flex-col md:flex-row flex-grow">
        {/* Left Section */}
        <div className="w-full md:w-1/2 p-6 md:p-16 flex flex-col">
          <div className="flex-grow flex flex-col justify-center mb-8 md:mb-0">
            <h1 className="text-5xl md:text-6xl font-bold mb-8 leading-tight">
              A Future of Personalization at Scale
            </h1>
            <p className="text-xl md:text-2xl leading-relaxed mb-12">
              Every customer should feel like the only customer. Smart systems, real-time insights, and seamless experiences make that possible—at any scale. Growth no longer means losing the personal touch. It means strengthening it.
            </p>
          </div>                    
        </div>
        
        {/* Right Section - Image */}
        <div className="hidden md:block md:w-1/2">
          <div className="h-full relative">
                        
            <img 
              src={HeroImg}
              alt="Village on hillside with clouds and sky" 
              className="h-full w-full object-cover"
            />
          </div>
        </div>
      </main>
      
      {/* Bottom Image for Mobile */}
      <div className="md:hidden w-full h-64">
        <img 
          src={HeroImg} 
          alt="Village on hillside with clouds and sky" 
          className="w-full h-full object-cover"
        />
      </div>
    </div>
  );
};

export default App;