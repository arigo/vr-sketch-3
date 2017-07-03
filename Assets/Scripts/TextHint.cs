using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using BaroqueUI;
using System;

public class TextHint : WorldObject
{
    public TextMesh textMesh;
    public Color nonSelectedColor, selectedColor;

    int ignore_controller_num = -1;
    int manual_enter_token = -1;

    private void Start()
    {
        var ct = Controller.HoverTracker(this);
        ct.SetPriority(-5);
        ct.onLeave += Ct_onLeave;
        ct.onMoveOver += Ct_onMoveOver;
        ct.onTouchDown += Ct_onDown;
        ct.onTriggerDown += Ct_onDown;
    }

    bool IgnoreController(Controller controller)
    {
        var world = GetComponentInParent<WorldScript>();
        return manual_enter_token < 0 ||
            world.CheckController(controller, ignore_controller_num) ||
            world.IsCurrentlyFrozenBy() != null;
    }

    private void Ct_onDown(Controller controller)
    {
        if (IgnoreController(controller))
            return;

        var world = GetComponentInParent<WorldScript>();
        GameObject keypad = Instantiate(world.distanceKeypadPrefab);
        Vector3 forward = transform.position - Baroque.GetHeadTransform().position;
        keypad.transform.rotation = Quaternion.LookRotation(forward);

        forward *= 0.2f;
        if (forward.magnitude > 0.14f)
            forward *= 0.14f / forward.magnitude;
        keypad.transform.position = transform.position - forward;

        keypad.GetComponent<KeyboardClicker>().onKeyboardTyping.AddListener(Kp_onKeyboardTyping);

        world.SetFrozenBy(keypad);
        textMesh.color = nonSelectedColor;
    }

    void AcceptKey(float factor)
    {
        var world = GetComponentInParent<WorldScript>();
        GameObject keypad = world.IsCurrentlyFrozenBy();
        if (keypad == null)
            return;

        var input_field = keypad.GetComponentInChildren<UnityEngine.UI.InputField>();
        if (input_field == null)
            return;

        float value;
        if (!float.TryParse(input_field.text, out value))
            return;
        value *= factor;

        world.UnFreeze();
        world.ManualEnter(manual_enter_token, value);
    }

    private void Kp_onKeyboardTyping(KeyboardClicker.EKeyState keystate, string ignored)
    {
        switch (keystate)
        {
            case KeyboardClicker.EKeyState.Special_Tab:    /* "cm" key */
                AcceptKey(0.01f);
                break;

            case KeyboardClicker.EKeyState.Special_Enter:    /* "m" key */
                AcceptKey(1f);
                break;
        }
    }

    private void Ct_onLeave(Controller controller)
    {
        textMesh.color = nonSelectedColor;
    }

    private void Ct_onMoveOver(Controller controller)
    {
        if (IgnoreController(controller))
            textMesh.color = nonSelectedColor;
        else
            textMesh.color = selectedColor;
    }

    public override void UpdateWorldObject(float[] data)
    {
        int index = 0;
        textMesh.text = GetString(data, ref index);
        Vector3 p1 = GetVec3(data, index);
        Vector3 p2 = GetVec3(data, index + 3);
        ignore_controller_num = (int)data[index + 6];
        manual_enter_token = (int)data[index + 7];

        transform.localPosition = (p1 + p2) * 0.5f;

        Vector3 p12 = transform.parent.TransformVector(p2 - p1);
        Vector3 pos2head = Baroque.GetHeadTransform().position - transform.position;
        Vector3 upwards = Vector3.Cross(pos2head, p12);
        Vector3 forward = Vector3.Cross(upwards, p12);
        if (upwards.y < -1e-3)
            upwards = -upwards;
        if (forward != Vector3.zero)
            transform.rotation = Quaternion.LookRotation(forward, upwards);

        float s = transform.parent.localScale.y;
        transform.localScale = Vector3.one / s;
    }
}
