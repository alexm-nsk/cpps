#ifndef SISAL_TYPES_H
#define SISAL_TYPES_H

#include <type_traits>


template<class T>
class SisalType{
private:
    T value;
public:
    bool error;
    template <typename R>
    constexpr SisalType<T> operator/(SisalType<R> const& rhs) noexcept
    {
        SisalType<T> result;
        if (rhs.get() == 0)
        {
            result.error = true;
            result = -12345;
        }
        else {
            result= get() / rhs.get();
        }
        return result;
    }
    template <typename R>
    constexpr SisalType<T> operator/(R const& rhs) noexcept
    {
        SisalType<T> result;
        if (rhs == 0)
        {
            result.error = true;
            result = -12345;
        }
        else {
            result= get() / rhs;
        }
        return result;
    }
    operator T(){
        return value;
    }
    operator Json::Value(){
        return value;
    }
    SisalType &operator = (const T &&new_value)
    {
        value = new_value;
        return *this;
    }
    template <typename R>
    SisalType &operator += (const R &&new_value)
    {
        value += new_value;
        return *this;
    }
    template <typename R>
    SisalType &operator += (const SisalType<R> &new_value)
    {
        error |= new_value.error;
        value += new_value.value;
        return *this;
    }
    template <typename R>
    SisalType &operator *= (SisalType <R> &&new_value)
    {
        error |= new_value.error;
        value *= new_value.value;
        return *this;
    }

    template <typename R>
    SisalType &operator *= (R &&new_value)
    {
        value *= new_value;
        return *this;
    }
    template <typename R>
    SisalType &operator -= (const R &&new_value)
    {
        value -= new_value;
        return *this;
    }
    template <typename R>
    SisalType &operator -= (SisalType <R> &&new_value)
    {
        error |= new_value.error;
        value -= new_value.value;
        return *this;
    }
    inline SisalType(T init){
        value = init;
        error = false;
    }
    SisalType(){
        value = 0;
        error = false;
    }
    T inline get() const
    {
        return value;
    }
    void set_error()
    {
        error = true;
    }
};

// -

template <typename T, typename N>
requires std::is_floating_point_v<N>
    SisalType <N>
    operator-(SisalType<T> const& lhs, SisalType<N> const& rhs) noexcept {
    SisalType <N> result = lhs.get() - rhs.get();
    result.error = lhs.error | rhs.error;
    return result;
}

template <typename T, typename N>
    SisalType <T>
    operator-(SisalType<T> const& lhs, SisalType<N> const& rhs) noexcept {
    SisalType <T> result = lhs.get() - rhs.get();
    result.error = lhs.error | rhs.error;
    return result;
}

//+

template <typename T, typename N>
requires std::is_floating_point_v<N>
constexpr     SisalType <N>
 operator+(SisalType<T> const& lhs, SisalType<N> const& rhs) noexcept {
    SisalType <N> result = lhs.get() + rhs.get();
    result.error = lhs.error | rhs.error;
    return result;
}

template <typename T, typename N>
constexpr SisalType <T> operator + (SisalType<T> const& lhs, SisalType<N> const& rhs) noexcept {
    SisalType <T> result = lhs.get() + rhs.get();
    result.error = lhs.error | rhs.error;
    return result;
}

//*

template <typename T, typename N>
requires std::is_floating_point_v<N>
constexpr SisalType<N> operator*(SisalType<T> const& lhs, SisalType<N> const& rhs) noexcept {
    SisalType <T> result = lhs.get() * rhs.get();
    result.error = lhs.error | rhs.error;
    return result;
}

template <typename T, typename N>
constexpr SisalType<T> operator*(SisalType<T> const& lhs, SisalType<N> const& rhs) noexcept {
    SisalType <T> result = lhs.get() * rhs.get();
    result.error = lhs.error | rhs.error;
    return result;
}

//  |

template <typename T, typename N>
requires std::is_floating_point_v<N>
constexpr SisalType<N> operator|(SisalType<T> const& lhs, SisalType<N> const& rhs) noexcept {
    return lhs.get() | rhs.get();
}

template <typename T, typename N>
constexpr SisalType<T> operator|(SisalType<T> const& lhs, SisalType<N> const& rhs) noexcept {
    return lhs.get() | rhs.get();
}


using namespace std;

template <typename T>
class Array{
    private:
        vector<T> value;
    public:
        bool error;
        Array ()
        {
            error = false;
        }

        Array (vector<T> init)
        {
            value = init;
            error = false;
        }

        inline operator vector<T>(){
            return value;
        }

        Array &operator = (const vector<T> &&new_value)
        {
            value = new_value;
            return *this;
        }

        T operator [] (int index)
        {
            return value[index];
        }

        inline vector<T> get()
        {
            return value;
        }

        Array<T> &operator || (const vector<T> &&appended)
        {
            value.insert(value.end(), appended.begin(), appended.end());
            return *this;
        }

        inline void push_back(T item)
        {
            value.push_back(item);
        }

        inline void push_front(T item)
        {
            value.insert(value.begin(), item);
        }

        inline void pop_back()
        {
            value.pop_back();
        }

        inline void pop_front()
        {
            value.erase(value.begin());
        }

        inline unsigned int size()
        {
            return value.size();
        }
        void set_error()
        {
            for(auto &item: value)
            {
                item.set_error();
            }
            error = true;
        }
};

typedef SisalType<int> integer;
typedef SisalType<float> real;
typedef SisalType<bool> boolean;

#pragma omp declare reduction (sis_product:integer:omp_out*=omp_in) initializer (omp_priv=1)
#pragma omp declare reduction (sis_product:real : omp_out = omp_out * omp_in) initializer (omp_priv=1)
#pragma omp declare reduction (sis_sum:integer:omp_out+=omp_in) initializer (omp_priv=0)
#pragma omp declare reduction (sis_sum:real : omp_out = omp_out + omp_in) initializer (omp_priv=0)

#endif
