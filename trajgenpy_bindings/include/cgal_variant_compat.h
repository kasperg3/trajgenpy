#ifndef CGAL_VARIANT_COMPAT_H
#define CGAL_VARIANT_COMPAT_H

#include <CGAL/version.h>
#include <boost/variant.hpp>

// CGAL 6.0+ uses std::variant, earlier versions use boost::variant
#if CGAL_VERSION_NR >= 1060000000
    #include <variant>
    #define CGAL_USES_STD_VARIANT 1
#else
    #define CGAL_USES_STD_VARIANT 0
#endif

namespace cgal_compat {

// Template function to get value from either boost::variant or std::variant
// Works like std::get_if or boost::get for pointer access

#if CGAL_USES_STD_VARIANT
    // For CGAL 6.0+ with std::variant
    template<typename T, typename... Types>
    inline T* get_variant(std::variant<Types...>* var) {
        return std::get_if<T>(var);
    }
    
    template<typename T, typename... Types>
    inline const T* get_variant(const std::variant<Types...>* var) {
        return std::get_if<T>(var);
    }
#else
    // For CGAL 5.x with boost::variant
    template<typename T, typename... Types>
    inline T* get_variant(boost::variant<Types...>* var) {
        return boost::get<T>(var);
    }
    
    template<typename T, typename... Types>
    inline const T* get_variant(const boost::variant<Types...>* var) {
        return boost::get<T>(var);
    }
#endif

} // namespace cgal_compat

#endif // CGAL_VARIANT_COMPAT_H
