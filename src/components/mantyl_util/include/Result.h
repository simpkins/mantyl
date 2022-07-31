// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <variant>

namespace mantyl {

template <typename T, typename E = esp_err_t> class Result {
public:
  using value_type = T;
  using error_type = E;
  enum ValueConstructor { ConstructValue };
  enum ErrorConstructor { ConstructError };

  Result() noexcept = default;
  Result(ValueConstructor, value_type &&value)
      : data_{std::in_place_index<1>, std::move(value)} {}
  Result(ValueConstructor, const value_type &value)
      : data_{std::in_place_index<1>, value} {}
  Result(ErrorConstructor, error_type &&error)
      : data_{std::in_place_index<0>, std::move(error)} {}
  Result(ErrorConstructor, const error_type &error)
      : data_{std::in_place_index<0>, error} {}

  bool has_value() const {
    return data_.index() == 1;
  }
  bool has_error() const {
    return data_.index() == 0;
  }

  const value_type& value() const {
    assert(has_value());
    return std::get<1>(data_);
  }
  const error_type& error() const {
    assert(has_error());
    return std::get<0>(data_);
  }

private:
  std::variant<error_type, value_type> data_;
};

template<typename T, typename E = esp_err_t>
Result<std::remove_reference_t<T>, std::remove_reference_t<E>> make_result(T&& value) {
  using ResultType = Result<std::remove_reference_t<T>, std::remove_reference_t<E>>;
  return ResultType{ResultType::ConstructValue, std::forward<T>(value)};
}

template<typename T, typename E>
Result<std::remove_reference_t<T>, std::remove_reference_t<E>> make_error(E&& error) {
  using ResultType = Result<std::remove_reference_t<T>, std::remove_reference_t<E>>;
  return ResultType{ResultType::ConstructError, std::forward<E>(error)};
}

template <typename T, typename E = esp_err_t>
bool operator==(const Result<T, E> &a, const Result<T, E> &b) {
  if (a.has_error()) {
    if (!b.has_error()) {
      return false;
    }
    return a.error() == b.error();
  }
  if (a.has_value()) {
    if (!b.has_value()) {
      return false;
    }
    return a.value() == b.value();
  }
  return false;
}

template <typename T, typename E = esp_err_t>
bool operator!=(const Result<T, E> &a, const Result<T, E> &b) {
  return !(a == b);
}

} // namespace mantyl
