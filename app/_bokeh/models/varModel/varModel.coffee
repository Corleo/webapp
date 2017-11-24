import {Model} from "model"
import * as p from "core/properties"

export class VarModel extends Model
  type: 'VarModel'

  @define {
      value: [ p.Any, null ]
  }

  initialize: (attrs, options) ->
    super(attrs, options)
