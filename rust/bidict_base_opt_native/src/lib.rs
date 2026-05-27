#![allow(
    clippy::useless_conversion,
    reason = "PyO3 #[pyfunction] expansion triggers this false positive on PyResult returns"
)]

use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::types::PyType;

#[derive(Clone, Copy)]
enum OnDupAction {
    Raise,
    DropOld,
    DropNew,
}

impl OnDupAction {
    fn parse(value: &str) -> PyResult<Self> {
        match value {
            "RAISE" => Ok(Self::Raise),
            "DROP_OLD" => Ok(Self::DropOld),
            "DROP_NEW" => Ok(Self::DropNew),
            _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
                "unknown OnDupAction: {value}"
            ))),
        }
    }
}

fn bidict_err<A>(py: Python<'_>, name: &str, args: A) -> PyErr
where
    A: pyo3::PyErrArguments + Send + Sync + 'static,
{
    let bidict = py
        .import_bound("bidict")
        .expect("bidict should already be importable");
    let err_type = bidict
        .getattr(name)
        .expect("bidict exception should already be importable")
        .downcast_into::<PyType>()
        .expect("bidict exception should be a Python type");
    PyErr::from_type_bound(err_type, args)
}

fn apply_item(
    py: Python<'_>,
    fwd: &Bound<'_, PyDict>,
    inv: &Bound<'_, PyDict>,
    key: &Bound<'_, PyAny>,
    val: &Bound<'_, PyAny>,
    on_dup_key: OnDupAction,
    on_dup_val: OnDupAction,
) -> PyResult<()> {
    let oldval = fwd.get_item(key)?.map(Bound::unbind);
    let oldkey = inv.get_item(val)?.map(Bound::unbind);
    let isdupkey = oldval.is_some();
    let isdupval = oldkey.is_some();

    if isdupkey && isdupval {
        let oldkey = oldkey.as_ref().expect("checked is_some above");
        let oldval = oldval.as_ref().expect("checked is_some above");
        if key.eq(oldkey.bind(py))? {
            assert!(val.eq(oldval.bind(py))?);
            return Ok(());
        }
        match on_dup_val {
            OnDupAction::Raise => {
                return Err(bidict_err(
                    py,
                    "KeyAndValueDuplicationError",
                    (key.clone().unbind(), val.clone().unbind()),
                ));
            }
            OnDupAction::DropNew => return Ok(()),
            OnDupAction::DropOld => {}
        }
    } else if isdupkey {
        match on_dup_key {
            OnDupAction::Raise => {
                return Err(bidict_err(
                    py,
                    "KeyDuplicationError",
                    (key.clone().unbind(),),
                ));
            }
            OnDupAction::DropNew => return Ok(()),
            OnDupAction::DropOld => {}
        }
    } else if isdupval {
        match on_dup_val {
            OnDupAction::Raise => {
                return Err(bidict_err(
                    py,
                    "ValueDuplicationError",
                    (val.clone().unbind(),),
                ));
            }
            OnDupAction::DropNew => return Ok(()),
            OnDupAction::DropOld => {}
        }
    }

    fwd.set_item(key, val)?;
    inv.set_item(val, key)?;

    if isdupkey && isdupval {
        let oldkey = oldkey.as_ref().expect("checked is_some above");
        let oldval = oldval.as_ref().expect("checked is_some above");
        fwd.del_item(oldkey.bind(py))?;
        inv.del_item(oldval.bind(py))?;
    } else if isdupkey {
        let oldval = oldval.as_ref().expect("checked is_some above");
        inv.del_item(oldval.bind(py))?;
    } else if isdupval {
        let oldkey = oldkey.as_ref().expect("checked is_some above");
        fwd.del_item(oldkey.bind(py))?;
    }

    Ok(())
}

fn apply_items(
    py: Python<'_>,
    fwd: &Bound<'_, PyDict>,
    inv: &Bound<'_, PyDict>,
    items: Bound<'_, PyAny>,
    on_dup_key: OnDupAction,
    on_dup_val: OnDupAction,
) -> PyResult<()> {
    for item in items.iter()? {
        let item = item?;
        let (key, val): (Py<PyAny>, Py<PyAny>) = item.extract()?;
        apply_item(
            py,
            fwd,
            inv,
            key.bind(py),
            val.bind(py),
            on_dup_key,
            on_dup_val,
        )?;
    }

    Ok(())
}

fn apply_mapping(
    py: Python<'_>,
    fwd: &Bound<'_, PyDict>,
    inv: &Bound<'_, PyDict>,
    mapping: Bound<'_, PyAny>,
    on_dup_key: OnDupAction,
    on_dup_val: OnDupAction,
) -> PyResult<()> {
    if let Ok(dict) = mapping.downcast::<PyDict>() {
        for (key, val) in dict.iter() {
            apply_item(py, fwd, inv, &key, &val, on_dup_key, on_dup_val)?;
        }
    } else {
        let items = mapping.call_method0("items")?;
        apply_items(py, fwd, inv, items, on_dup_key, on_dup_val)?;
    }

    Ok(())
}

#[pyfunction]
fn build_bidict_maps(
    py: Python<'_>,
    items: Bound<'_, PyAny>,
    on_dup_key: &str,
    on_dup_val: &str,
) -> PyResult<(Py<PyDict>, Py<PyDict>)> {
    let on_dup_key = OnDupAction::parse(on_dup_key)?;
    let on_dup_val = OnDupAction::parse(on_dup_val)?;
    let fwd = PyDict::new_bound(py);
    let inv = PyDict::new_bound(py);

    apply_items(py, &fwd, &inv, items, on_dup_key, on_dup_val)?;

    Ok((fwd.unbind(), inv.unbind()))
}

#[pyfunction]
fn build_bidict_maps_from_mapping(
    py: Python<'_>,
    mapping: Bound<'_, PyAny>,
    on_dup_key: &str,
    on_dup_val: &str,
) -> PyResult<(Py<PyDict>, Py<PyDict>)> {
    let on_dup_key = OnDupAction::parse(on_dup_key)?;
    let on_dup_val = OnDupAction::parse(on_dup_val)?;
    let fwd = PyDict::new_bound(py);
    let inv = PyDict::new_bound(py);

    apply_mapping(py, &fwd, &inv, mapping, on_dup_key, on_dup_val)?;

    Ok((fwd.unbind(), inv.unbind()))
}

#[pyfunction]
fn update_bidict_maps(
    py: Python<'_>,
    fwd: Bound<'_, PyDict>,
    inv: Bound<'_, PyDict>,
    items: Bound<'_, PyAny>,
    on_dup_key: &str,
    on_dup_val: &str,
) -> PyResult<(Py<PyDict>, Py<PyDict>)> {
    let on_dup_key = OnDupAction::parse(on_dup_key)?;
    let on_dup_val = OnDupAction::parse(on_dup_val)?;
    let new_fwd = fwd.copy()?;
    let new_inv = inv.copy()?;

    apply_items(py, &new_fwd, &new_inv, items, on_dup_key, on_dup_val)?;

    Ok((new_fwd.unbind(), new_inv.unbind()))
}

#[pyfunction]
fn update_bidict_maps_from_mapping(
    py: Python<'_>,
    fwd: Bound<'_, PyDict>,
    inv: Bound<'_, PyDict>,
    mapping: Bound<'_, PyAny>,
    on_dup_key: &str,
    on_dup_val: &str,
) -> PyResult<(Py<PyDict>, Py<PyDict>)> {
    let on_dup_key = OnDupAction::parse(on_dup_key)?;
    let on_dup_val = OnDupAction::parse(on_dup_val)?;
    let new_fwd = fwd.copy()?;
    let new_inv = inv.copy()?;

    apply_mapping(py, &new_fwd, &new_inv, mapping, on_dup_key, on_dup_val)?;

    Ok((new_fwd.unbind(), new_inv.unbind()))
}

#[pymodule]
fn bidict_base_opt_native(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(build_bidict_maps, module)?)?;
    module.add_function(wrap_pyfunction!(build_bidict_maps_from_mapping, module)?)?;
    module.add_function(wrap_pyfunction!(update_bidict_maps, module)?)?;
    module.add_function(wrap_pyfunction!(update_bidict_maps_from_mapping, module)?)?;
    Ok(())
}
